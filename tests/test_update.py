""""""

# Standard library modules.

# Third party modules.
import pytest
import sqlalchemy

# Local modules.
import dataclasses_sql

# Globals and constants variables.


@pytest.fixture
def metadata():
    engine = sqlalchemy.create_engine("sqlite:///:memory:")
    return sqlalchemy.MetaData(engine)


def test_update_no_data(metadata, treedata):
    with pytest.raises(ValueError):
        dataclasses_sql.update(metadata, treedata)


def test_update(metadata, treedata):
    # Insert
    assert treedata.diameter_m == pytest.approx(3.0, abs=1e-4)
    success = dataclasses_sql.insert(metadata, treedata)
    assert success

    # Update
    treedata.serial_number = 2  # key field
    treedata.diameter_m = 4.0  # non-key field

    success = dataclasses_sql.update(metadata, treedata)
    assert success

    # Check
    with metadata.bind.begin() as conn:
        rows = conn.execute("select * from treedata").fetchall()

    assert len(rows) == 1

    row = rows[0]
    assert row["serial_number"] == 2
    assert row["specie"] == "Hibiscus abelmoschus"
    assert row["diameter_m"] == pytest.approx(4.0, abs=1e-2)
    assert (
        row["long_description"]
        == b"Hibiscus is a genus of flowering plants in the mallow family, Malvaceae."
    )
    assert row["has_flower"]
    assert row["plantation_datetime"] == "2019-07-21 18:54:21.000000"
    assert row["last_pruning_date"] == "2019-08-01"
