# Grist FDW for PostgreSQL

[![Run tests](https://github.com/johncant/gristfdw/actions/workflows/tests.yml/badge.svg)](https://github.com/johncant/gristfdw/actions/workflows/tests.yml)

This is a Grist Foreign Data Wrapper for PostgreSQL

### State of development

WIP. This FDW only supports Grist types Text, Numeric, Int, Bool, and Date so far.

The column name `id` is reserved for the Grist record id

## Installation

### Native installation

#### 1. Install PostgreSQL 13 (DELETE does not work with 14+)

#### 2. Install [Multicorn 2](https://github.com/pgsql-io/multicorn2)

The original Multicorn doesn't support newer potsgreSQL versions and seems to have a different python API. Tested with Multicorn 2.4

#### 3. Install this python package to your system

#### 4. Install [this branch](https://github.com/johncant/py_grist_api/tree/jc_add_list_tables_columns) of `py_grist_api

### Docker image

The dockerfile for gristfdw just builds an extension of the `postgres` docker image. These dockerfiles are in `docker/` in this repo

## Usage

Run this kind of SQL

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

## Production deployment

Use this in production at your own risk.

Extending postgres using C extensions is risky, and a database is one place where risk tolerance should be low.

Thanks to Multicorn, the risk of segfaults should be contained within Multicorn. However, caution is advised.

One way to contain the risk of unreliability would be to run the gristfdw docker container (based on postgres), as a proxy to Grist.

```
# Example only
docker run -it \
           -ePOSTGRES_PASSWORD=<REPLACE_ME> \
           -ePOSTGRES_USER=gristfdw \
           -ePOSTGRES_DB=gristfdw \
           -p5433:5432 \
           gristfdw:main-bullseye-postgres13-multicorn2.4
```

Now, set up gristfdw

```
$ psql postgres://gristfdw:<REPLACE_ME>@localhost:5433/gristfdw

CREATE EXTENSION multicorn;
DROP SERVER IF EXISTS test CASCADE;
CREATE SERVER test FOREIGN DATA WRAPPER multicorn OPTIONS (
  wrapper 'gristfdw.GristForeignDataWrapper',
  api_key YOUR_API_KEY,
  doc_id YOUR_GRIST_DOC_ID,
  server YOUR_GRIST_SERVER
);
IMPORT FOREIGN SCHEMA foo FROM SERVER test INTO public;
```

Example only. Log into your production DB and use postgres_fdw to talk to our proxy

```
CREATE SERVER grist_proxy
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (...);

CREATE USER MAPPING ...

IMPORT FOREIGN SCHEMA ... FROM SERVER grist_proxy INTO ...
```

The risk of database downtime is now contained.

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
