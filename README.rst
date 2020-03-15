===============
dataclasses-sql
===============

.. image:: https://img.shields.io/pypi/v/dataclasses_sql.svg
        :target: https://pypi.python.org/pypi/dataclasses_sql

.. image:: https://img.shields.io/travis/ppinard/dataclasses_sql.svg
        :target: https://travis-ci.org/ppinard/dataclasses_sql

.. image:: https://readthedocs.org/projects/dataclasses-sql/badge/?version=latest
        :target: https://dataclasses-sql.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

Using dataclasses with SQL databases.

Examples::

    import dataclasses
    import sqlalchemy
    import sqlalchemy_dataclasses.sql as sql

    @dataclasses.dataclass
    class Car:
        brand: str = dataclasses.field(metadata={"key": True})
        model: str = dataclasses.field(metadata={"key": True})
        milage: float

    # Connect to database
    engine = sqlalchemy.create_engine("sqlite:///:memory:")
    metadata = sqlalchemy.MetaData(engine)

    # Create table
    table = sql.require_table(metadata, Car)
    print(table.columns)

    # Insert data
    car = Car("Kia", "Ceed", 15678)
    sql.insert(metdata, car, check_exists=True)

Installation
============

Easiest way to install using ``pip``::

    pip install dataclasses_sql

For development installation from the git repository::

    git clone git@github.com/ppinard/dataclasses_sql.git
    cd dataclasses_sql
    pip install -e .

Release notes
=============

0.1.0
-----


Contributors
============


License
=======

The library is provided under the MIT license license.

Copyright (c) 2020, Philippe Pinard





