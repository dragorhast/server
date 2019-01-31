"""
Fields
-------

Defines some additional fields so that the Schemas can
serialize to and from additional native python data types.
"""

from enum import Enum, IntEnum
from typing import Union, Optional, Type

from marshmallow import fields, ValidationError


class Bytes(fields.Field):
    """
    A field that serializes :class:`bytes` or a hex-encoded :class:`str`
    to a hex-encoded :class:`str` and de-serializes it back to :class:`bytes`.
    """

    def __init__(self, *args, max_length: Optional[int] = None, as_string=False, **kwargs):
        """
        :param max_length: The maximum length of the hex-encoded string.
        :param as_string: Whether to serialize to and from hex-string instead of bytes.
        """
        super().__init__(*args, **kwargs)
        self.max_length = max_length
        self.as_string = as_string

    def _serialize(self, value: Union[str, bytes], attr, obj, **kwargs) -> str:
        """Converts a bytes-like-string or byte array to a hex-encoded string."""
        if isinstance(value, bytes):
            value = value.hex()
        elif isinstance(value, str):
            try:
                int(value, 16)
            except ValueError:
                raise ValidationError(f"String {value} is not a valid hex-encoded string.", value)
        else:
            raise ValidationError(f"Only accepts type str or bytes, not {type(value)}")

        if self.max_length and len(value) > self.max_length:
            raise ValidationError(f"Bytes field too long ({len(value)} instead of {self.max_length})")

        return value

    def _deserialize(self, value: str, attr, data, **kwargs) -> Union[str, bytes]:
        """Converts a hex-encoded string to bytes or a bytes-like-string."""
        try:
            int(value, 16)
        except ValueError:
            raise ValidationError(f"String {value} is not a valid hex-encoded string.")

        if self.as_string:
            return value if self.as_string else bytes.fromhex(value)
        else:
            return bytes.fromhex(value)

    @staticmethod
    def _jsonschema_type_mapping():
        """Defines the jsonschema type for the object."""
        return {
            'type': 'string',
        }


class EnumField(fields.Field):
    """
    A field that serializes an :class:`~enum.Enum` to a :class:`str` and back.
    """

    def __init__(self, enum_type: Type[Enum], *args, use_name=False, as_string=False, **kwargs):
        """
        :param enum_type: the :class:`~enum.Enum` (or :class:`~enum.IntEnum`) subclass
        :param use_name: use enum's property name instead of value when serialize
        :param as_string: serialize value as string
        """
        super().__init__(*args, **kwargs)
        if not issubclass(enum_type, Enum):
            raise ValidationError(f"Expected enum type, got {type(enum_type)} instead")
        self._enum_type = enum_type
        self.use_name = use_name
        self.as_string = as_string

    def _serialize(self, value: Union[Enum, str], attr, obj, **kwargs):
        """Converts an enum to a string representation."""
        if isinstance(value, str) and value in (enum.value for enum in self._enum_type):
            return value
        elif isinstance(value, self._enum_type):
            if self.use_name:
                return value.name
            if self.as_string:
                return str(value.value)
            return value.value
        return None

    def _deserialize(self, value: str, attr, data, **kwargs) -> Optional[Enum]:
        """Converts a string back to the enum type T."""
        try:
            if self.use_name:
                return self._enum_type[value]
            if issubclass(self._enum_type, IntEnum):
                return self._enum_type(int(value))
            if issubclass(self._enum_type, Enum):
                return self._enum_type(value)
        except Exception:
            raise ValidationError(f"Field does not exist on {self._enum_type}.")
        else:
            return None

    def _jsonschema_type_mapping(self):
        """Defines the jsonschema type for the object."""
        return {
            'type': 'string',
            'enum': [enum.value for enum in self._enum_type]
        }


def Many(schema):
    return fields.List(fields.Nested(schema))
