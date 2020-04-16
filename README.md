# dataclasses-sql

[![Build Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fppinard%2Fdataclasses-sql%2Fbadge&style=flat)](https://actions-badge.atrox.dev/ppinard/dataclasses-sql/goto)

Using dataclasses with SQL databases.

Examples:

```python
import dataclasses
import sqlalchemy
import dataclasses_sql

@dataclasses.dataclass
class Car:
    brand: str = dataclasses.field(metadata={"key": True})
    model: str = dataclasses.field(metadata={"key": True})
    milage: float

# Connect to database
engine = sqlalchemy.create_engine("sqlite:///:memory:")
metadata = sqlalchemy.MetaData(engine)
metadata.reflect()

# Insert
car = Car("Kia", "Ceed", 15678)
dataclasses_sql.insert(metadata, car, check_exists=True)

car = Car("Ford", "Mustang", 4032)
dataclasses_sql.insert(metadata, car, check_exists=True)

# Select
builder = dataclasses_sql.SelectStatementBuilder()
builder.add_column(Car, "mileage")
builder.add_clause(Car, "brand", "Kia")
statement = builder.build()

with metadata.bind.begin() as conn:
    row = conn.execute(statement).fetchone()
    print(row)
```

## Installation

Easiest way to install using *pip*:

```
pip install dataclasses-sql
```

For development installation from the git repository::

```
git clone git@github.com/ppinard/dataclasses-sql.git
cd dataclasses-sql
pip install -e .
```

## Release notes

### 0.1.0


## Contributors


## License

The library is provided under the MIT license license.

Copyright (c) 2020, Philippe Pinard





