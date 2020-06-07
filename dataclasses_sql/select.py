""""""

# Standard library modules.
import dataclasses
import operator
import typing

# Third party modules.
import sqlalchemy.sql

# Local modules.
from .base import get_table_name

# Globals and constants variables.
_OPERATION_LOOKUP = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "in": lambda column, value: column.in_(value),
    "notin": lambda column, value: column.notin_(value),
    "is": lambda column, value: column.is_(value),
    "isnot": lambda column, value: column.isnot(value),
}


def _check_column_exists(dataclass, column_name):
    field_names = set(field.name for field in dataclasses.fields(dataclass))
    if not column_name.endswith("id") and column_name not in field_names:
        raise ValueError(f"Dataclass {dataclass.__name__} has no column {column_name}")


@dataclasses.dataclass
class _Clause:
    dataclass: dataclasses.dataclass
    column_name: str
    value: typing.Any
    operation: typing.Any


class SelectStatementBuilder:
    def __init__(self, distinct=False):
        self.distinct = distinct

        self._tables = set()
        self._columns = []
        self._joins = {}
        self._clauses = []

    def add_column(self, dataclass, column_name, label=None):
        # Check column exist
        _check_column_exists(dataclass, column_name)

        # Add column
        self._tables.add(dataclass)
        self._columns.append((dataclass, column_name, label))

    def add_all_columns(self, dataclass):
        # Add table
        self._tables.add(dataclass)

        # Add id column
        self._columns.append((dataclass, "id", None))

        # Add column for each field
        for field in dataclasses.fields(dataclass):
            if dataclasses.is_dataclass(field.type):
                self._columns.append((dataclass, f"{field.name}_id", None))
            else:
                self._columns.append((dataclass, field.name, None))

    def add_join(
        self,
        dataclass_left,
        dataclass_right,
        outer=False,
        column_name_left=None,
        column_name_right=None,
    ):
        if dataclass_left == dataclass_right:
            raise ValueError("Left and right cannot be the same dataclass")

        if column_name_right is None:
            column_name_right = "id"

        # Find corresponding field in the left dataclass
        if column_name_left is None:
            for field in dataclasses.fields(dataclass_left):
                if field.type == dataclass_right:
                    column_name_left = f"{field.name}_id"
                    break

            if column_name_left is None:
                raise ValueError(
                    f"Cannot find a field with dataclass {dataclass_right} in {dataclass_left}"
                )
        else:
            _check_column_exists(dataclass_left, column_name_left)

        # Add
        self._tables.add(dataclass_left)
        self._tables.add(dataclass_right)
        self._joins[(dataclass_left, dataclass_right)] = (
            column_name_left,
            column_name_right,
            outer,
        )

    def add_clause(self, *args):
        if not args:
            raise ValueError("Missing clause argument")

        elif isinstance(args[0], _Clause):
            clauses = args

        else:
            clauses = (self.create_clause(*args),)

        for clause in clauses:
            self._tables.add(clause.dataclass)
        self._clauses.append(tuple(clauses))

    def create_clause(self, dataclass, column_name, value, operation="=="):
        # Check column exist
        _check_column_exists(dataclass, column_name)

        # Check operation:
        if operation not in _OPERATION_LOOKUP:
            valid_operations_str = ", ".join(_OPERATION_LOOKUP.keys())
            raise ValueError(
                f"Unknown operation: {operation}, valid operations: {valid_operations_str}"
            )

        return _Clause(dataclass, column_name, value, operation)

    def build(self):
        # Checks
        if not self._tables:
            raise ValueError("No table in select")

        # Create table lookup
        sqltables = {}
        for dataclass in self._tables:
            table_name = get_table_name(dataclass)
            sqltable = sqlalchemy.sql.table(table_name)
            sqltables[dataclass] = sqltable

        # Create columns
        sqlcolumns = []
        for dataclass, column_name, label in self._columns:
            sqltable = sqltables[dataclass]
            sqlcolumn = sqlalchemy.sql.column(column_name, _selectable=sqltable)

            if label is not None:
                sqlcolumn = sqlcolumn.label(label)

            sqlcolumns.append(sqlcolumn)

        # Create statement
        statement = sqlalchemy.sql.select(sqlcolumns, distinct=self.distinct)

        # Add join
        if self._joins:
            # Create SQL joins
            sqljoins = []

            for (
                (dataclass_left, dataclass_right),
                (column_name_left, column_name_right, outer),
            ) in self._joins.items():
                sqltable_left = sqltables[dataclass_left]
                sqltable_right = sqltables[dataclass_right]

                sqlcolumn_left = sqlalchemy.sql.column(
                    column_name_left, _selectable=sqltable_left
                )
                sqlcolumn_right = sqlalchemy.sql.column(
                    column_name_right, _selectable=sqltable_right
                )

                onclause = sqlcolumn_left == sqlcolumn_right
                sqljoins.append((sqltable_left, sqltable_right, onclause, outer))

            # Create select from statement
            # Joins have to be nested to work with sqlalchemy
            # E.g.
            # j = table_a.join(
            #        table_b.join(table_c,
            #            table_b.c.id == table_c.c.b_id),
            #        table_b.c.a_id == table_a.c.id)
            sqltable_left, sqltable_right, onclause, outer = sqljoins[0]

            if outer:
                finaljoin = sqltable_left.outerjoin(sqltable_right, onclause)
            else:
                finaljoin = sqltable_left.join(sqltable_right, onclause)

            for _, sqltable_right, onclause, outer in sqljoins[1:]:
                if outer:
                    finaljoin = finaljoin.outerjoin(sqltable_right, onclause)
                else:
                    finaljoin = finaljoin.join(sqltable_right, onclause)

            statement = statement.select_from(finaljoin)

        # Create clauses
        sqlclauses = []
        for clauses_or in self._clauses:
            sqlclauses_or = []
            for clause in clauses_or:
                sqltable = sqltables[clause.dataclass]
                sqlcolumn = sqlalchemy.sql.column(
                    clause.column_name, _selectable=sqltable
                )
                sqlclause = _OPERATION_LOOKUP[clause.operation](sqlcolumn, clause.value)
                sqlclauses_or.append(sqlclause)

            sqlclauses.append(sqlalchemy.sql.or_(*sqlclauses_or))

        return statement.where(sqlalchemy.sql.and_(*sqlclauses))
