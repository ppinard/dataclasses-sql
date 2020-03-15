""""""

# Standard library modules.
import dataclasses
import datetime

# Third party modules.

# Local modules.

# Globals and constants variables.


@dataclasses.dataclass
class TaxonomyData:
    kingdom: str = dataclasses.field(metadata={"key": True})
    order: str = dataclasses.field(metadata={"key": True})
    family: str = dataclasses.field(metadata={"key": True})
    genus: str = dataclasses.field(metadata={"key": True})


@dataclasses.dataclass
class TreeData:
    serial_number: int = dataclasses.field(metadata={"key": True})
    taxonomy: TaxonomyData = dataclasses.field(metadata={"key": True})
    specie: str = dataclasses.field(metadata={"key": True})
    diameter_m: float = None
    long_description: bytes = None
    has_flower: bool = None
    plantation_datetime: datetime.datetime = None
    last_pruning_date: datetime.date = None
