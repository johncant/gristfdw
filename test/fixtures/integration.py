from test.defaults import (GRIST_API_KEY, GRIST_DOC_ID,
                           GRIST_SERVER_FROM_LOCAL, GRIST_SERVER_FROM_POSTGRES,
                           POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_PORT,
                           POSTGRES_USER)

import psycopg2
import pytest
from grist_api import GristDocAPI


@pytest.fixture
def conn():
    """
    Connection to postgres with multicorn and gristfdw installed
    """
    with psycopg2.connect(f"postgres://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}") as c:

        with c.cursor() as cur:
            cur.execute("""
                CREATE EXTENSION IF NOT EXISTS multicorn;
            """)

        yield c


@pytest.fixture
def server(conn):
    """
    Sets up our external server in postgres
    """
    with conn.cursor() as cur:
        cur.execute(f"DROP SERVER IF EXISTS test")

    with conn.cursor() as cur:
        cur.execute(f"""
            CREATE SERVER test FOREIGN DATA WRAPPER multicorn OPTIONS (
              wrapper 'gristfdw.GristForeignDataWrapper',
              api_key '{GRIST_API_KEY}',
              doc_id '{GRIST_DOC_ID}',
              server '{GRIST_SERVER_FROM_POSTGRES}'
            );
        """)

    yield "test"

    with conn.cursor() as cur:
        cur.execute(f"DROP SERVER IF EXISTS test CASCADE")


@pytest.fixture
def schema(conn):
    name = "gristfdw_schema"

    with conn.cursor() as cur:
        cur.execute(f"""DROP SCHEMA IF EXISTS {name};""")

    with conn.cursor() as cur:
        cur.execute(f"""CREATE SCHEMA {name};""")

    yield name

    with conn.cursor() as cur:
        cur.execute(f"""DROP SCHEMA IF EXISTS {name} CASCADE;""")


@pytest.fixture
def simple_table(conn, server, table_name):

    with conn.cursor() as cur:
        cur.execute("DROP FOREIGN TABLE IF EXISTS \"{table_name}\"")
    with conn.cursor() as cur:
        cur.execute(f"""
            CREATE FOREIGN TABLE \"{table_name}\" (
                id BIGINT,
                col1 TEXT,
                col2 FLOAT,
                col3 BIGINT,
                col4 BOOLEAN,
                col5 DATE,
                col9 BIGINT,
                col10 BIGINT[]
            )
            SERVER {server}
            OPTIONS (table_name '{table_name}')
        """)
    yield
    with conn.cursor() as cur:
        cur.execute("DROP FOREIGN TABLE IF EXISTS \"{table_name}\" CASCADE")


@pytest.fixture
def grist_api(monkeypatch):
    monkeypatch.setenv("GRIST_API_KEY", GRIST_API_KEY)
    return GristDocAPI(GRIST_DOC_ID, server=GRIST_SERVER_FROM_LOCAL)


@pytest.fixture
def assert_grist_table(table_name, grist_api):
    def inner(expected):
        actual = grist_api.fetch_table(table_name)

        # Convert namedtuples to dicts
        # Filter out gristHelper_display, which is for reference columns
        actual_asdict = [
            {
                k: v
                for k, v in t._asdict().items()
                if not k.startswith("gristHelper_Display")
            }
            for t in actual
        ]

        assert actual_asdict == expected

    return inner
