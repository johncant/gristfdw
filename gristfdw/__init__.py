from datetime import date, datetime, timezone

from grist_api import GristDocAPI
from multicorn import ColumnDefinition, ForeignDataWrapper, TableDefinition

REQUIRED_OPTIONS=["doc_id", "server", "api_key"]


def null_passthrough(func):
    """
    Decorator for handling None conveniently
    """
    def inner(val):
        if val is None:
            return None
        return func(val)

    return inner


def column_definition_grist_to_postgres(table, column):
    def mkcol(**options):
        return ColumnDefinition(
            column_name=column['id'],
            **options
        )

    fields = column['fields']

    if 'type' not in fields:
        raise ValueError(fields)

    if fields['type'] == 'Text':
        return mkcol(type_name='TEXT')
    elif fields['type'] == 'Numeric':
        return mkcol(type_name="FLOAT")
    elif fields['type'] == 'Int':
        return mkcol(type_name="BIGINT")
    elif fields['type'] == 'Bool':
        return mkcol(type_name="BOOLEAN")
    elif fields['type'] == 'Date':
        return mkcol(type_name="DATE")
    elif fields['type'].startswith("Ref:"):
        # Reference col. We can get the table name from `type`
        # However, we don't really need it. This column is a foreign
        # key into another table. However, Grist does not impose constraints,
        # so there is no point in us doing that.
        return mkcol(type_name="BIGINT")
    # Any, Datetime, Choice, Choicelist, Ref, Reflist, Attachments not yet
    # supported
    else:
        raise ValueError(
            f"Unsupported column type \"{fields['type']}\" "
            f"for table \"{table}\" "
            f"column \"{column['id']}\""
        )


def table_definition_grist_to_postgres(table, columns):
    id_column = ColumnDefinition(
        column_name='id',
        type_name='BIGINT',
    )

    return TableDefinition(
        table_name=table['id'],
        columns=[id_column]+[
            column_definition_grist_to_postgres(table, column)
            for column in columns
        ],
        options={"table_name": table['id']}
    )


@null_passthrough
def postgres_boolean_to_grist(val):
    # Postgres returns 't' or 'f'
    # Grist wants a boolean
    if val == 't':
        return True
    elif val == 'f':
        return False
    else:
        raise ValueError(f"No conversion defined for postgres value \"{val}\"")


@null_passthrough
def grist_date_to_postgres(val):
    # Grist returns a unix timestamp
    # Multicorn wants a date
    # We can't use date.fromtimestamp or datetime.fromtimestamp, since these
    # use the local timezone to map to a date.
    return datetime.utcfromtimestamp(val).date()


@null_passthrough
def postgres_date_to_grist(val):
    # Postgres/multicorn return a date
    # Grist wants a unix timestamp
    # Grist's API uses timestamps representing midnight UTC.
    return int(
        datetime(
            val.year, val.month, val.day,
            0, 0, 0,
            tzinfo=timezone.utc
        ).timestamp()
    )


@null_passthrough
def postgres_int_to_grist(val):
    return int(val)


class GristForeignDataWrapper(ForeignDataWrapper):

    def __init__(self, options, columns):
        super(GristForeignDataWrapper, self).__init__(options, columns)
        self.options = options
        self.columns = columns
        self.table_name = self.options.pop('table_name')
        self.grist = GristDocAPI(**self.options)

    @property
    def rowid_column(self):
        return 'id'

    @classmethod
    def validate_options(cls, options):
        passed_options = set(options.keys())

        missing_options = set(REQUIRED_OPTIONS) - passed_options
        invalid_options = set(passed_options) - set(REQUIRED_OPTIONS)

        missing_error = ""
        invalid_error = ""

        if len(missing_options) > 0:
            missing_error = f"Missing required options {missing_options}"

        if len(invalid_error) > 0:
            invalid_error = f"Invalid options {invalid_options}"

        if missing_error or invalid_error:
            raise ValueError(missing_error+". "+invalid_error)

    @classmethod
    def import_schema(cls, schema, srv_options, options, restriction_type, restricts):
        cls.validate_options(srv_options)
        grist = GristDocAPI(**srv_options)

        return [
            table_definition_grist_to_postgres(
                table=table,
                columns=grist.columns(table['id'])['columns'],
            )
            for table in grist.tables()['tables']
        ]

    def row_grist_to_postgres(self, record):
        postgres_record = {}

        for k, v in record._asdict().items():
            if k not in self.columns:
                # ignored, like manualSort
                continue
            elif v is None:
                postgres_record[k] = None
            elif self.columns[k].type_name.upper() == "DATE":
                postgres_record[k] = grist_date_to_postgres(v)
            else:
                postgres_record[k] = v

        return postgres_record

    def row_postgres_to_grist(self, record):
        grist_record = {}

        for k, v in record.items():
            if self.columns[k].type_name.upper() == "BOOLEAN":
                grist_record[k] = postgres_boolean_to_grist(v)
            elif self.columns[k].type_name.upper() == "DATE":
                grist_record[k] = postgres_date_to_grist(v)
            elif self.columns[k].type_name.upper() == "BIGINT":
                grist_record[k] = postgres_int_to_grist(v)
            else:
                grist_record[k] = v

        return grist_record

    def execute(self, quals, columns):
        # TODO - pass quals
        return [
            self.row_grist_to_postgres(rec)
            for rec in self.grist.fetch_table(self.table_name)
        ]

    def insert(self, new_values):
        assert new_values['id'] is None
        del new_values['id']

        results = self.grist.add_records(
            self.table_name,
            [self.row_postgres_to_grist(new_values)]
        )
        new_id = results[0]

        return dict(
            id=new_id,
            **new_values
        )

    def update(self, id_, new_values):
        assert id_ == new_values["id"]
        new_values['id'] = int(new_values['id'])
        results = self.grist.update_records(
            self.table_name,
            record_dicts=[self.row_postgres_to_grist(new_values)]
        )
        return new_values

    def delete(self, rowid):
        # TODO - this does not work as expected with postgres 14+. It tries to
        # delete row 0
        self.grist.delete_records(self.table_name, record_ids=[int(rowid)])
