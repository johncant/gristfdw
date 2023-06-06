# Grist FDW for PostgreSQL

This is a Grist Foreign Data Wrapper for PostgreSQL

### State of development

WIP. This FDW only supports Grist types Text, Numeric, Int, and Bool so far.

Also, deletes do not yet work as expected.

The column name `id` is reserved for the Grist record id

### How to use

#### 1. Install PostgreSQL

#### 2. Install [Multicorn 2](https://github.com/pgsql-io/multicorn2)

The original Multicorn doesn't support newer potsgreSQL versions and seems to have a different python API

#### 3. Install this python package to your system

#### 4. Install [this branch](https://github.com/johncant/py_grist_api/compare/jc_add_list_tables_columns?expand=1) of `py_grist_api`

#### 5. Run this kind of SQL

```sql
-- Load multicorn
CREATE EXTENSION multicorn;

-- Pass options to this FDW
CREATE SERVER test FOREIGN DATA WRAPPER multicorn OPTIONS (
  wrapper 'gristfdw.GristForeignDataWrapper',
  api_key YOUR_API_KEY,
  doc_id YOUR_GRIST_DOC_ID,
  server YOUR_GRIST_SERVER
);

-- Make your grist tables into PostgreSQL
IMPORT FOREIGN SCHEMA foo FROM SERVER test INTO public;

-- Example
SELECT * FROM Table1
```

### License

GPLv3

### Contributing

Contributions welcome!
