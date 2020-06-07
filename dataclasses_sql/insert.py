""""""

# Standard library modules.
import dataclasses

# Third party modules.
from loguru import logger

# Local modules.
from .base import require_table, get_rowid

# Globals and constants variables.


def insert(metadata, data, check_exists=True):
    """
    Insert a dataclass instance into database.
    Returns ``True`` if successful.
    """
    # Check if exists
    if hasattr(data, "_rowid"):
        return False

    if check_exists:
        rowid = get_rowid(metadata, data)
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
    table = require_table(metadata, data)

    with metadata.bind.begin() as conn:
        result = conn.execute(
            table.insert(), row
        )  # pylint: disable=no-value-for-parameter
        logger.debug(f"Added {data} to table {table.name}")
        rowid = result.inserted_primary_key[0]
        data._rowid = rowid
        return True


def exists(metadata, data):
    return get_rowid(metadata, data) is not None
