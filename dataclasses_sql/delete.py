""""""

# Standard library modules.

# Third party modules.
from loguru import logger

# Local modules.
from .base import get_rowid, require_table

# Globals and constants variables.


def delete(metadata, data):
    """
    Remove a dataclass instance from database.
    Returns ``True`` if successful.
    """
    # Find if data exists
    rowid = get_rowid(metadata, data)
    if rowid is None:
        raise ValueError("Data does not exists")

    # Insert
    table = require_table(metadata, data)

    with metadata.bind.begin() as conn:
        conn.execute(table.delete().where(table.c.id == rowid))
        logger.debug(f"Deleted {data} to table {table.name}")
        return True
