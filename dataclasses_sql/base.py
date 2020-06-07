""""""

# Standard library modules.
import dataclasses
import datetime
import re
import inspect

# Third party modules.
import sqlalchemy.sql
from loguru import logger

# Local modules.

# Globals and constants variables.

TYPE_TO_SQLTYPE = {
    int: sqlalchemy.Integer,
    float: sqlalchemy.Float,
    str: sqlalchemy.String,
    bytes: sqlalchemy.LargeBinary,
    datetime.datetime: sqlalchemy.DateTime,
    datetime.date: sqlalchemy.Date,
    bool: sqlalchemy.Boolean,
}


def camelcase_to_words(text):
    return re.sub("([a-z0-9])([A-Z])", r"\1 \2", text)


def iskeyfield(field):
    return field.name.startswith("key") or field.metadata.get("key", False)


def keyfields(dataclass):
    return tuple(field for field in dataclasses.fields(dataclass) if iskeyfield(field))


def get_table_name(data_or_dataclass):
    if not inspect.isclass(data_or_dataclass):
        data_or_dataclass = type(data_or_dataclass)

    name = data_or_dataclass.__name__.lower()
    return "_".join(camelcase_to_words(name).split())


def require_table(metadata, data_or_dataclass):
    """
    Creates a table based on the dataclass, if it doesn't already exist in the database.
    """
    table_name = get_table_name(data_or_dataclass)
    table = metadata.tables.get(table_name)

    if table is None:
        table = create_table(metadata, table_name, data_or_dataclass)

    return table


def create_table(metadata, table_name, data_or_dataclass):
    # Add column for key fields of inputdata and all fields of outputdata.
    columns = [sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True)]

    for field in dataclasses.fields(data_or_dataclass):
        columns.append(_create_column(metadata, field))

    # Create table.
    table = sqlalchemy.Table(table_name, metadata, *columns)
    metadata.create_all(tables=[table])
    logger.debug(f'Create table "{table_name}"')

    return table


def _create_column(metadata, field):
    if dataclasses.is_dataclass(field.type):
        subtable = require_table(metadata, field.type)
        return sqlalchemy.Column(
            field.name + "_id", None, sqlalchemy.ForeignKey(subtable.name + ".id")
        )

    if issubclass(field.type, str) and iskeyfield(field):
        column_type = sqlalchemy.String(collation="NOCASE")
    elif field.type in TYPE_TO_SQLTYPE:
        column_type = TYPE_TO_SQLTYPE.get(field.type)
    else:
        raise ValueError(f"Cannot convert {field.name} to SQL column")

    nullable = field.default is None

    return sqlalchemy.Column(field.name, column_type, nullable=nullable)


def get_rowid(metadata, data):
    """
    Returns the row of the dataclass if it exists.
    If not, ``None`` is returned
    Args:
        data (dataclasses.dataclass): instance
    Returns:
        int: row of the dataclass instance in its table, ``None`` if not found
    """
    if hasattr(data, "_rowid"):
        return data._rowid

    # Find table
    table_name = get_table_name(data)
    table = metadata.tables.get(table_name)
    if table is None:
        return None

    # Construct where statement
    clauses = []
    for field in keyfields(data):
        value = getattr(data, field.name)

        if dataclasses.is_dataclass(field.type):
            rowid = get_rowid(metadata, value)
            clause = table.c[field.name + "_id"] == rowid
        else:
            clause = table.c[field.name] == value

        clauses.append(clause)

    if not clauses:
        raise ValueError(f"Dataclass {data.__class__.__name__} has no key fields")

    # Execute
    statement = sqlalchemy.sql.select([table.c.id]).where(sqlalchemy.sql.and_(*clauses))
    logger.debug("Find statement: {}", str(statement.compile()).replace("\n", ""))

    with metadata.bind.begin() as conn:
        rowid = conn.execute(statement).scalar()
        if not rowid:
            return None

        data._rowid = rowid
        return rowid
