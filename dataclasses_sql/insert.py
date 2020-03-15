""""""

# Standard library modules.
import dataclasses
import datetime

# Third party modules.
import sqlalchemy.sql
from loguru import logger

# Local modules.
from .utils import iskeyfield, keyfields, get_table_name

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


def insert(metadata, data, check_exists=True):
    """
    Insert a dataclass instance into database.
    Returns ``True`` if successful.
    """
    # Check if exists
    if hasattr(data, "_rowid"):
        return False

    if check_exists:
        rowid = _get_rowid(metadata, data)
        if rowid is not None:
            return False

    # Create row
    row = {}
    for field in dataclasses.fields(data):
        name = field.name
        value = getattr(data, name)

        if dataclasses.is_dataclass(value):
            insert(metadata, value, check_exists)
            row[name + "_id"] = int(value._rowid)
        else:
            row[name] = value

    # Insert
    table = _require_table(metadata, data)

    with metadata.bind.begin() as conn:
        result = conn.execute(
            table.insert(), row
        )  # pylint: disable=no-value-for-parameter
        logger.debug(f"Added {data} to table {table.name}")
        rowid = result.inserted_primary_key[0]
        data._rowid = rowid
        return True


def exists(metadata, data):
    return _get_rowid(metadata, data) is not None


def _require_table(metadata, data_or_dataclass):
    """
    Creates a table based on the dataclass, if it doesn't already exist in the database.
    """
    table_name = get_table_name(data_or_dataclass)
    table = metadata.tables.get(table_name)

    if table is None:
        table = _create_table(metadata, table_name, data_or_dataclass)

    return table


def _create_table(metadata, table_name, data_or_dataclass):
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
        subtable = _require_table(metadata, field.type)
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


def _get_rowid(metadata, data):
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

    table_name = get_table_name(data)
    table = metadata.tables.get(table_name)
    if table is None:
        return None

    clauses = []
    for field in keyfields(data):
        value = getattr(data, field.name)

        if dataclasses.is_dataclass(field.type):
            rowid = _get_rowid(metadata, value)
            clause = table.c[field.name + "_id"] == rowid
        else:
            clause = table.c[field.name] == value

        clauses.append(clause)

    if not clauses:
        logger.debug("No key fields")
        return None

    statement = sqlalchemy.sql.select([table.c.id]).where(sqlalchemy.sql.and_(*clauses))
    logger.debug("Find statement: {}", str(statement.compile()).replace("\n", ""))

    with metadata.bind.begin() as conn:
        rowid = conn.execute(statement).scalar()
        if not rowid:
            return None

        data._rowid = rowid
        return rowid
