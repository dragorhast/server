"""
Defines some additional fields so that the Schemas can serialize to and from native python data types.
"""

from enum import Enum, IntEnum
from typing import Union, Optional, Type

from marshmallow import fields, ValidationError


class BytesField(fields.Field):
    """
    A field that serializes :class:`bytes` or a hex-encoded :class:`str`
    to a hex-encoded :class:`str` and de-serializes it back to :class:`bytes`.
    """

    def __init__(self, *args, max_length: Optional[int] = None, **kwargs):
        """
        :param max_length: The maximum length of the hex-encoded string.
        """
        super().__init__(*args, **kwargs)
        self.max_length = max_length

    def _serialize(self, value: Union[str, bytes], attr, obj, **kwargs):
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

    def _deserialize(self, value: str, attr, data, **kwargs):
        """Converts a hex-encoded string to a bytes-like object."""
        try:
            return bytes.fromhex(value)
        except ValueError:
            raise ValidationError(f"String {value} is not a valid hex-encoded string.")

    def _jsonschema_type_mapping(self):
        """Defines the jsonschema type for the object."""
        return {
            'type': 'string',
        }


class EnumField(fields.Field):
    """
    A fields the serializes an :class:`Enum` to a :class:`str` and back.
    """

    def __init__(self, enum_type: Type[Enum], *args, use_name=False, as_string=False, **kwargs):
        """
        :param enum_type: theEnum (or enum.IntEnum) subclass
        :param use_name: use enum's property name instead of value when serialize
        :param as_string: serialize value as string
        """
        super().__init__(*args, **kwargs)
        if not issubclass(enum_type, Enum):
            raise ValidationError(f"Expected enum type, got {type(enum_type)} instead")
        self._enum_type = enum_type
        self.use_name = use_name
        self.as_string = as_string

    def _serialize(self, value: Enum, attr, obj, **kwargs):
        """Converts an enum to a string representation."""
        if value is not None:
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