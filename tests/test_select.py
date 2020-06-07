""""""

# Standard library modules.

# Third party modules.
import pytest
import sqlalchemy

# Local modules.
import dataclasses_sql
from .data import TreeData, TaxonomyData

# Globals and constants variables.


@pytest.fixture
def metadata(treedata):
    engine = sqlalchemy.create_engine("sqlite:///:memory:")
    metadata = sqlalchemy.MetaData(engine)
    metadata.reflect()

    dataclasses_sql.insert(metadata, treedata)

    data = TaxonomyData("plantae", "rosales", "rosaceae", "rosa")
    dataclasses_sql.insert(metadata, data)

    return metadata


def test_add_column_field():
    builder = dataclasses_sql.SelectStatementBuilder()
    builder.add_column(TreeData, "specie")
    builder.build()

    assert len(builder._tables) == 1
    assert len(builder._columns) == 1


def test_add_column_missing():
    builder = dataclasses_sql.SelectStatementBuilder()

    with pytest.raises(ValueError):
        builder.add_column(TreeData, "doesnotexist")


def test_add_column_dataclass():
    builder = dataclasses_sql.SelectStatementBuilder()
    builder.add_column(TreeData, "taxonomy")
    builder.build()

    assert len(builder._tables) == 1
    assert len(builder._columns) == 1


def test_add_all_columns():
    builder = dataclasses_sql.SelectStatementBuilder()
    builder.add_all_columns(TaxonomyData)
    builder.build()

    assert len(builder._tables) == 1
    assert len(builder._columns) == 5


def test_add_join():
    builder = dataclasses_sql.SelectStatementBuilder()
    builder.add_all_columns(TreeData)
    builder.add_join(TreeData, TaxonomyData)
    builder.build()

    assert len(builder._joins) == 1


def test_add_join_invalid():
    builder = dataclasses_sql.SelectStatementBuilder()

    with pytest.raises(ValueError):
        builder.add_join(TaxonomyData, TreeData)


def test_add_join_specific_column():
    builder = dataclasses_sql.SelectStatementBuilder()
    builder.add_all_columns(TreeData)
    builder.add_join(TreeData, TaxonomyData, column_name_left="taxonomy")
    builder.build()

    assert len(builder._joins) == 1


@pytest.mark.parametrize("operation", ["==", "!=", ">", ">=", "<", "<="])
def test_add_clause(operation):
    builder = dataclasses_sql.SelectStatementBuilder()
    builder.add_all_columns(TreeData)
    builder.add_clause(TreeData, "diameter_m", 3, operation)
    builder.build()

    assert len(builder._clauses) == 1


def test_add_clause_in():
    builder = dataclasses_sql.SelectStatementBuilder()
    builder.add_all_columns(TreeData)
    builder.add_clause(TreeData, "diameter_m", [3, 4, 5], "in")
    builder.build()

    assert len(builder._clauses) == 1


def test_select(metadata):
    builder = dataclasses_sql.SelectStatementBuilder()
    builder.add_all_columns(TaxonomyData)
    statement = builder.build()

    with metadata.bind.begin() as conn:
        rows = conn.execute(statement).fetchall()

    assert len(rows) == 2


def test_select_with_label(metadata):
    builder = dataclasses_sql.SelectStatementBuilder()
    builder.add_column(TaxonomyData, "order", label="foo")
    statement = builder.build()

    with metadata.bind.begin() as conn:
        rows = conn.execute(statement).fetchall()

    assert len(rows) == 2
    assert "foo" in rows[0].keys()


def test_select_with_join(metadata):
    builder = dataclasses_sql.SelectStatementBuilder()
    builder.add_column(TreeData, "specie")
    builder.add_column(TaxonomyData, "genus")
    builder.add_join(TreeData, TaxonomyData)
    statement = builder.build()

    with metadata.bind.begin() as conn:
        rows = conn.execute(statement).fetchall()

    assert len(rows) == 1


def test_select_with_clause(metadata):
    builder = dataclasses_sql.SelectStatementBuilder()
    builder.add_all_columns(TaxonomyData)
    builder.add_clause(TaxonomyData, "genus", "rosa")
    statement = builder.build()

    with metadata.bind.begin() as conn:
        rows = conn.execute(statement).fetchall()

    assert len(rows) == 1


def test_select_with_clauses(metadata):
    builder = dataclasses_sql.SelectStatementBuilder()
    builder.add_all_columns(TaxonomyData)

    clause1 = builder.create_clause(TaxonomyData, "genus", "rosa")
    clause2 = builder.create_clause(TaxonomyData, "genus", "hibiscus")
    builder.add_clause(clause1, clause2)

    statement = builder.build()

    with metadata.bind.begin() as conn:
        rows = conn.execute(statement).fetchall()

    assert len(rows) == 2


def test_select_with_join_and_clause(metadata):
    builder = dataclasses_sql.SelectStatementBuilder()
    builder.add_all_columns(TreeData)
    builder.add_join(TreeData, TaxonomyData)
    builder.add_clause(TreeData, "diameter_m", 3, ">=")
    statement = builder.build()

    with metadata.bind.begin() as conn:
        rows = conn.execute(statement).fetchall()

    assert len(rows) == 1
