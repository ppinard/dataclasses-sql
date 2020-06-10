""""""

# Standard library modules.
import dataclasses

# Third party modules.
from loguru import logger

# Local modules.
from .base import get_rowid, require_table
from .insert import insert

# Globals and constants variables.


def update(metadata, data):
    """
    Update a dataclass instance into database.
    Returns ``True`` if successful.
    """
    # Find if data exists
    rowid = get_rowid(metadata, data)
    if rowid is None:
        raise ValueError("Data does not exists")

    # Create row
    row = {}
    for field in dataclasses.fields(data):
        name = field.name
        value = getattr(data, name)

        if dataclasses.is_dataclass(value):
            insert(metadata, value, check_exists=False)
            row[name + "_id"] = int(value._rowid)
        else:
            row[name] = value

    # Update
    table = require_table(metadata, data)

    with metadata.bind.begin() as conn:
        conn.execute(table.update().where(table.c.id == rowid), row)
        logger.debug(f"Updated {data} to table {table.name}")
        return True
