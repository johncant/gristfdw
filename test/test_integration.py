import psycopg2

def test_IMPORT_FOREIGN_SCHEMA():
    with psycopg2.connect("postgres://gristfdw:secret@localhost:5433") as conn:
        
        with conn.cursor() as cur:
            cur.execute("""
                CREATE EXTENSION multicorn;
            """)
        with conn.cursor() as cur:
            cur.execute("""
                CREATE SERVER test FOREIGN DATA WRAPPER multicorn OPTIONS (
                  wrapper 'gristfdw.GristForeignDataWrapper',
                  api_key 'REDACTED',
                  doc_id 'REDACTED',
                  server 'REDACTED'
                );
            """)
            #cur.fetchall()
    #import pdb; pdb.set_trace()

