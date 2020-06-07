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


def test_insert(metadata, treedata):
    success = dataclasses_sql.insert(metadata, treedata)
    assert success

    # Check treedata table
    with metadata.bind.begin() as conn:
        rows = conn.execute("select * from treedata").fetchall()

    assert len(rows) == 1

    row = rows[0]
    assert row["serial_number"] == 1
    assert row["specie"] == "Hibiscus abelmoschus"
    assert row["diameter_m"] == pytest.approx(3.0, abs=1e-2)
    assert (
        row["long_description"]
        == b"Hibiscus is a genus of flowering plants in the mallow family, Malvaceae."
    )
    assert row["has_flower"]
    assert row["plantation_datetime"] == "2019-07-21 18:54:21.000000"
    assert row["last_pruning_date"] == "2019-08-01"

    # Check taxonomy table
    with metadata.bind.begin() as conn:
        rows = conn.execute("select * from taxonomydata").fetchall()

    assert len(rows) == 1

    row = rows[0]

    assert row["kingdom"] == "plantae"
    assert row["order"] == "malvales"
    assert row["family"] == "malvaceae"
    assert row["genus"] == "hibiscus"


def test_insert_check_exists_using_rowid(metadata, treedata):
    success = dataclasses_sql.insert(metadata, treedata)
    assert success

    success = dataclasses_sql.insert(metadata, treedata)
    assert not success


def test_insert_check_exists_using_database(metadata, treedata):
    success = dataclasses_sql.insert(metadata, treedata)
    assert success

    del treedata._rowid
    del treedata.taxonomy._rowid
    success = dataclasses_sql.insert(metadata, treedata)
    assert not success


def test_exists(metadata, treedata):
    assert not dataclasses_sql.exists(metadata, treedata)

    success = dataclasses_sql.insert(metadata, treedata)
    assert success
    assert dataclasses_sql.exists(metadata, treedata)
