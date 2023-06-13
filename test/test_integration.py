import psycopg2


# These settings are associated with data in test/fixtures/grist_persist
GRIST_API_KEY="23c5ae3adcda4890d2d8c51faddbe12bdd4b36a9"
GRIST_DOC_ID="qS2YtmEG67cFjbgBBaooFQ"
GRIST_SERVER="http://grist:8484"


def test_IMPORT_FOREIGN_SCHEMA():

    with psycopg2.connect("postgres://gristfdw:secret@localhost:5433") as conn:

        with conn.cursor() as cur:
            cur.execute("""
                CREATE EXTENSION multicorn;
            """)

        with conn.cursor() as cur:
            cur.execute(f"""
                CREATE SERVER test FOREIGN DATA WRAPPER multicorn OPTIONS (
                  wrapper 'gristfdw.GristForeignDataWrapper',
                  api_key '{GRIST_API_KEY}',
                  doc_id '{GRIST_DOC_ID}',
                  server '{GRIST_SERVER}'
                );
            """)

        with conn.cursor() as cur:
            cur.execute(f"""DROP SCHEMA IF EXISTS gristfdw_test_ifs;""")

        with conn.cursor() as cur:
            cur.execute(f"""CREATE SCHEMA gristfdw_test_ifs;""")

        with conn.cursor() as cur:
            cur.execute(f"""IMPORT FOREIGN SCHEMA ignored FROM SERVER test INTO gristfdw_test_ifs;""")

        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'gristfdw_test_ifs';
            """)
            table_names = [name for name, in cur.fetchall()]

        assert "Test_SELECT" in table_names
        assert "Test_INSERT" in table_names
        assert "Test_UPDATE" in table_names
        assert "Test_DELETE" in table_names
