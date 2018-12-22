from enum import Enum
from typing import TypeVar

from tortoise import ConfigurationError
from tortoise.fields import CharField

T = TypeVar("T")


class EnumField(CharField):

    def __init__(self, enum_type: T, *args, **kwargs):
        super().__init__(128, *args, **kwargs)
        if not issubclass(enum_type, Enum):
            raise ConfigurationError(f"{enum_type} is not a subclass of Enum!")
        self._enum_type = enum_type

    def to_db_value(self, value: T, instance) -> str:
        return value.value

    def to_python_value(self, value: str) -> T:
        try:
            return self._enum_type(value)
        except Exception:
            raise ValueError(f"Database value {value} does not exist on Enum {self._enum_type}.")

