from multicorn import ForeignDataWrapper, TableDefinition, ColumnDefinition
from grist_api import GristDocAPI


REQUIRED_OPTIONS=["doc_id", "server", "api_key"]


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
    #  elif fields['type'] == 'Date':
    #      return mkcol(type_name="DATE")
    #  elif fields['type'].startswith('DateTime:'):
    #      # TODO - handle timezones
    #      return mkcol(type_name="TIMESTAMP")
    # Choice, Ref, Reflist, Attachments not yet supported
    else:
        raise ValueError(f"Unsupported column type \"{fields['type']}\" for table \"{table}\" column \"{column['id']}\"")


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
        return record._asdict()

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
            [new_values]
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
            record_dicts=[new_values]
        )
        return new_values

    def delete(self, rowid):
        # TODO - this does not work as expected. It tries to delete row 0
        self.grist.delete_records(self.table_name, record_ids=[int(rowid)])
