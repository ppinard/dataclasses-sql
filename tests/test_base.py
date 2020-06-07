""""""

# Standard library modules.
import dataclasses

# Third party modules.
import pytest

# Local modules.
from dataclasses_sql.base import iskeyfield, keyfields
from .data import TaxonomyData, TreeData

# Globals and constants variables.


@pytest.mark.parametrize("dataclass,expected", [(TaxonomyData, 4), (TreeData, 3)])
def test_iskeyfield(dataclass, expected):
    fields = dataclasses.fields(dataclass)
    keyfields = [field for field in fields if iskeyfield(field)]
    assert len(keyfields) == expected


@pytest.mark.parametrize("dataclass,expected", [(TaxonomyData, 4), (TreeData, 3)])
def test_keyfields(dataclass, expected):
    fields = keyfields(dataclass)
    assert len(fields) == expected
