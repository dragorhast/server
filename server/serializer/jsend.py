"""
JSend Schema
------------

Programmatically defines the JSend specification.
"""

from enum import Enum
from typing import Type

from marshmallow import Schema, fields, validates_schema, ValidationError

from .fields import EnumField


class JSendStatus(Enum):
    """Enumerates the JSend status states."""

    SUCCESS = "success"
    """Everything went as expected."""

    FAIL = "fail"
    """There was a user error with the request, or supplied data."""

    ERROR = "error"
    """There was a system error with the request."""


class JSendSchema(Schema):
    """
    A Schema that encapsulates the logic of the `JSend Format`_.

    .. _`JSend Format`: https://labs.omniti.com/labs/jsend
    """
    status = EnumField(JSendStatus, required=True)
    data = fields.Field()
    message = fields.String()
    code = fields.Integer()

    @validates_schema
    def assert_fields(self, data):
        """
        Asserts that, according to the specification:

        - the ``data`` field is included when the status is :attr:`~JSendStatus.SUCCESS` or :attr:`~JSendStatus.FAIL`
        - the ``message`` field is included when the status is :attr:`~JSendStatus.ERROR`
        """
        if data["status"] == JSendStatus.SUCCESS or data["status"] == JSendStatus.FAIL:
            if "data" not in data:
                raise ValidationError(f"When status is {data['status']}, the data field must be populated.")
        if data["status"] == JSendStatus.FAIL:
            if "message" not in data["data"]:
                raise ValidationError(f"All failures must return user-friendly error message.")
        if data["status"] == JSendStatus.ERROR:
            if "message" not in data:
                raise ValidationError(f"When the status is {data['status']}, the message fields must be populated.")

    @staticmethod
    def of(data_type: Type, *args, **kwargs):
        """
        Creates a subclass of JSendSchema of a specific data type.

        This allows us to require the ``data`` property to be of a specific schema.
        As an example, to create a JSendSchema that expects a BikeSchema as the data:

        >>> bike_schema = JSendSchema.of(BikeSchema())
        >>> validated_data = bike_schema.load(await response.json())
        """

        class TypedJSendSchema(JSendSchema):
            data = fields.Nested(data_type, *args, **kwargs)

        return TypedJSendSchema()
