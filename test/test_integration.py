import psycopg2
import pytest
from grist_api import GristDocAPI


# These settings are associated with data in test/fixtures/grist_persist
GRIST_API_KEY="23c5ae3adcda4890d2d8c51faddbe12bdd4b36a9"
GRIST_DOC_ID="qS2YtmEG67cFjbgBBaooFQ"
GRIST_SERVER_FROM_POSTGRES="http://grist:8484"
GRIST_SERVER_FROM_LOCAL="http://localhost:8484"


@pytest.fixture
def conn():
    """
    Connection to postgres with multicorn and gristfdw installed
    """
    with psycopg2.connect("postgres://gristfdw:secret@localhost:5433") as c:

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
                col4 BOOLEAN
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
        actual_asdict = [t._asdict() for t in actual]

        assert actual_asdict == expected

    return inner


def test_IMPORT_FOREIGN_SCHEMA(conn, server, schema):

    with conn.cursor() as cur:
        cur.execute(f"""IMPORT FOREIGN SCHEMA ignored FROM SERVER {server} INTO {schema};""")

    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = '{schema}';
        """)
        table_names = [name for name, in cur.fetchall()]

    assert "Test_SELECT" in table_names
    assert "Test_INSERT" in table_names
    assert "Test_UPDATE" in table_names
    assert "Test_DELETE" in table_names


@pytest.mark.parametrize('table_name', ["Test_SELECT"])
def test_SELECT(simple_table, table_name, conn):

    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT * FROM \"{table_name}\"
        """)
        data = cur.fetchall()

    assert len(data) == 1
    assert data[0] == (1, 'simple data', 3.6, 2, True)


@pytest.mark.parametrize('table_name', ["Test_INSERT"])
def test_INSERT(simple_table, table_name, conn, assert_grist_table):

    with conn.cursor() as cur:
        cur.execute(f"""
            INSERT INTO \"{table_name}\" (
                col1, col2, col3, col4
            ) VALUES (
                'inserted', 4.9, 5, false
            ) RETURNING id
        """)
        data = cur.fetchall()

    assert data == [(2,)]

    assert_grist_table([
        # Original row
        {
            'id': 1,
            'col1': 'simple data',
            'col2': 3.6,
            'col3': 2,
            'col4': True,
            'manualSort': 1,
        },
        # Newly inserted row
        {
            'id': 2,
            'col1': 'inserted',
            'col2': 4.9,
            'col3': 5,
            'col4': False,
            'manualSort': 2,
        }
    ])


@pytest.mark.parametrize('table_name', ["Test_UPDATE"])
def test_UPDATE(simple_table, table_name, conn, assert_grist_table):

    with conn.cursor() as cur:
        cur.execute(f"""
            UPDATE \"{table_name}\"
            SET col1 = 'updated',
                col2 = 4.9,
                col3 = 5,
                col4 = false
            WHERE id = 1
        """)

    assert_grist_table([
        # Updated row
        {
            'id': 1,
            'col1': 'updated',
            'col2': 4.9,
            'col3': 5,
            'col4': False,
            'manualSort': 1,
        },
    ])


# Failing on postgres 14+ with multicorn 2.4
@pytest.mark.parametrize('table_name', ["Test_DELETE"])
def test_DELETE(simple_table, table_name, conn, assert_grist_table):

    with conn.cursor() as cur:
        cur.execute(f"""
            DELETE FROM \"{table_name}\"
            WHERE id = 1
        """)

    assert_grist_table([])
