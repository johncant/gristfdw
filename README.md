# Grist FDW for PostgreSQL

[![Run tests](https://github.com/johncant/gristfdw/actions/workflows/tests.yml/badge.svg)](https://github.com/johncant/gristfdw/actions/workflows/tests.yml)

This is a Grist Foreign Data Wrapper for PostgreSQL

### State of development

WIP. This FDW only supports Grist types Text, Numeric, Int, and Bool so far.

The column name `id` is reserved for the Grist record id

### How to use

#### 1. Install PostgreSQL 13 (DELETE does not work with 14+)

#### 2. Install [Multicorn 2](https://github.com/pgsql-io/multicorn2)

The original Multicorn doesn't support newer potsgreSQL versions and seems to have a different python API. Tested with Multicorn 2.4

#### 3. Install this python package to your system

#### 4. Install [this branch](https://github.com/johncant/py_grist_api/tree/jc_add_list_tables_columns) of `py_grist_api`

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

## Contributing

Contributions welcome!

### Running the tests

1. Install this package 

```bash
python -m pip install -e .[test]
```

2. Run the tests

```bash
rm -rf test/grist_persist/ && cp -r test/fixtures/grist_persist/ test/ && tox
```

Arguments to tox after `--` are currently passed to pytest.

The tests use a docker container each for grist and postgres.

### Editing test data in Grist

This repo includes Grist data as a test fixture. To edit this data, run

```bash
scripts/edit_grist_fixture
```

This runs Grist and opens a browser tab.
