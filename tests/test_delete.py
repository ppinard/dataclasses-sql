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


def test_delete_no_data(metadata, treedata):
    with pytest.raises(ValueError):
        dataclasses_sql.update(metadata, treedata)


def test_delete(metadata, treedata):
    # Insert
    assert treedata.diameter_m == pytest.approx(3.0, abs=1e-4)
    success = dataclasses_sql.insert(metadata, treedata)
    assert success

    # Delete
    success = dataclasses_sql.delete(metadata, treedata)
    assert success

    # Check
    with metadata.bind.begin() as conn:
        rows = conn.execute("select * from treedata").fetchall()

    assert len(rows) == 0
