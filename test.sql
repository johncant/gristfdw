CREATE EXTENSION multicorn;
DROP SERVER IF EXISTS test CASCADE;
CREATE SERVER test FOREIGN DATA WRAPPER multicorn OPTIONS (
  wrapper 'gristfdw.GristForeignDataWrapper',
  api_key YOUR_API_KEY,
  doc_id YOUR_GRIST_DOC_ID,
  server YOUR_GRIST_SERVER
);
IMPORT FOREIGN SCHEMA foo FROM SERVER test INTO public;
SELECT * FROM information_schema.tables WHERE table_schema LIKE 'public' OR table_schema LIKE 'foo';
SELECT * FROM information_schema.columns WHERE table_name = 'Table1';
SELECT * FROM "Table1";
INSERT INTO "Table1" (col1, col2, col3, col4) VALUES ('foo', 1.2, 1, 'f');
SELECT * FROM "Table1";
UPDATE "Table1" SET col2 = -col2 WHERE col1 = 'foo' AND id % 2 = 0;
SELECT * FROM "Table1";
DELETE FROM "Table1" WHERE col2 > 0;
SELECT * FROM "Table1"
