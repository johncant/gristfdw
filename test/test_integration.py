from datetime import date, datetime
from test.fixtures.integration import (assert_grist_table, conn, grist_api,
                                       schema, server, simple_table)

import psycopg2
import pytest
from grist_api import GristDocAPI


def test_IMPORT_FOREIGN_SCHEMA(conn, server, schema, grist_api):

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
    assert data[0] == (1, 'simple data', 3.6, 2, True, date(2023, 5, 21))


@pytest.mark.parametrize('table_name', ["Test_INSERT"])
def test_INSERT(simple_table, table_name, conn, assert_grist_table):

    with conn.cursor() as cur:
        cur.execute(f"""
            INSERT INTO \"{table_name}\" (
                col1, col2, col3, col4, col5
            ) VALUES (
                'inserted', 4.9, 5, false, '2024-01-01'
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
            # TODO - potential issue. dates entered in Grist through the UI are
            # really timestamps for midnight in the client's timezone. This
            # could cause problems. There's no time zone field in the Grist
            # column information for date. Use Grist server/user info to
            # convert the date?

            # For now, we'll just set the expected value to this timestamp.
            'col5': int(datetime(2023, 5, 21, 1, 0, 0).timestamp()),
            'manualSort': 1,
        },
        # Newly inserted row
        {
            'id': 2,
            'col1': 'inserted',
            'col2': 4.9,
            'col3': 5,
            'col4': False,
            # TODO - unlike row 1, which we inserted through the Grist UI, row 2
            # was inserted via gristfdw. row 2 date time zone is UTC or time
            # zone naive. Grist has returned the value we inserted and not any
            # time zone. We might need to be aware of Grist's server time zone.

            # For now, we'll just set the document time zone to UTC.
            'col5': int(datetime(2024, 1, 1, 0, 0, 0).timestamp()),
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
                col4 = false,
                col5 = '2024-01-01'
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
            'col5': int(datetime(2024, 1, 1, 0, 0, 0).timestamp()),
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
