""""""

# Standard library modules.
import re
import dataclasses
import inspect

# Third party modules.

# Local modules.

# Globals and constants variables.


def camelcase_to_words(text):
    return re.sub("([a-z0-9])([A-Z])", r"\1 \2", text)


def iskeyfield(field):
    return field.name.startswith("key") or field.metadata.get("key", False)


def keyfields(dataclass):
    return tuple(field for field in dataclasses.fields(dataclass) if iskeyfield(field))


def get_table_name(data_or_dataclass):
    if not inspect.isclass(data_or_dataclass):
        data_or_dataclass = type(data_or_dataclass)

    name = data_or_dataclass.__name__.lower()
    return "_".join(camelcase_to_words(name).split())
