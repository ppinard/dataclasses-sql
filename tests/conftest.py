""""""

# Standard library modules.
import datetime

# Third party modules.
import pytest

# Local modules.
from .data import TaxonomyData, TreeData

# Globals and constants variables.


@pytest.fixture
def treedata():
    taxonomy = TaxonomyData("plantae", "malvales", "malvaceae", "hibiscus")
    return TreeData(
        1,
        taxonomy,
        "Hibiscus abelmoschus",
        diameter_m=3.0,
        long_description=b"Hibiscus is a genus of flowering plants in the mallow family, Malvaceae.",
        has_flower=True,
        plantation_datetime=datetime.datetime(2019, 7, 21, 18, 54, 21),
        last_pruning_date=datetime.datetime(2019, 8, 1, 13, 0, 5),
    )
