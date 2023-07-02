from datetime import date, datetime, timezone
from test.fixtures.integration import (assert_grist_table, conn, grist_api,
                                       schema, server, simple_table)
from test.helper import grist_date

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
    assert data[0] == (1, 'simple data', 3.6, 2, True, date(2023, 5, 21), 1, [1, 2, 3])


@pytest.mark.parametrize('table_name', ["Test_INSERT"])
def test_INSERT(simple_table, table_name, conn, assert_grist_table):

    with conn.cursor() as cur:
        cur.execute(f"""
            INSERT INTO \"{table_name}\" (
                col1, col2, col3, col4, col5, col9, col10
            ) VALUES (
                'inserted', 4.9, 5, false, '2024-01-01', 3, '{{2, 3}}'
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
            'col5': grist_date(2023, 5, 21),
            'col9': 1,
            'col10': ['L', 1, 2, 3],
            'manualSort': 1,
        },
        # Newly inserted row
        {
            'id': 2,
            'col1': 'inserted',
            'col2': 4.9,
            'col3': 5,
            'col4': False,
            'col5': grist_date(2024, 1, 1),
            'col9': 3,
            'col10': ['L', 2, 3],
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
                col5 = '2024-01-01',
                col9 = 2,
                col10 = '{{1}}'
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
            'col5': grist_date(2024, 1, 1),
            'col9': 2,
            'col10': ['L', 1],
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


@pytest.mark.parametrize('table_name', ["Test_SELECT_NULLs"])
def test_SELECT_NULLs(simple_table, table_name, conn):

    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT * FROM \"{table_name}\"
        """)
        data = cur.fetchall()

    assert len(data) == 1

    # Findings from writing this:
    #   - Grist doesn't allow null for Text columns, and defaults to ''
    #   - Grist doesn't allow null for Bool columns, and defaults to False
    #   - Grist doesn't allow null for RefList columns, and defaults to []
    assert data[0] == (1, '', None, None, False, None, 0, [])


@pytest.mark.parametrize('table_name', ["Test_INSERT_NULLs"])
def test_INSERT_NULLs(simple_table, table_name, conn, assert_grist_table):

    with conn.cursor() as cur:
        cur.execute(f"""
            INSERT INTO \"{table_name}\" (
                col1, col2, col3, col4, col5, col9, col10
            ) VALUES (
                NULL, NULL, NULL, NULL, NULL, NULL, NULL
            ) RETURNING id
        """)
        data = cur.fetchall()

    assert data == [(1,)]

    assert_grist_table([
        # Newly inserted row
        {
            'id': 1,
            # col1: Actually, when you delete Text values via the UI, you get ''
            'col1': None,
            'col2': None,
            'col3': None,
            'col4': False,
            'col5': None,
            'col9': 0,
            'col10': None,
            'manualSort': 1,
        }
    ])

@pytest.mark.parametrize('table_name', ["Test_UPDATE_NULLs"])
def test_UPDATE_NULLs(simple_table, table_name, conn, assert_grist_table):

    with conn.cursor() as cur:
        cur.execute(f"""
            UPDATE \"{table_name}\" SET
            col1 = NULL,
            col2 = NULL,
            col3 = NULL,
            col4 = NULL,
            col5 = NULL,
            col9 = NULL,
            col10 = NULL
        """)

    assert_grist_table([
        # Newly inserted row
        {
            'id': 1,
            # col1: Actually, when you delete Text values via the UI, you get ''
            'col1': None,
            'col2': None,
            'col3': None,
            'col4': False,
            'col5': None,
            'col9': 0,
            'col10': None,
            'manualSort': 1,
        }
    ])
