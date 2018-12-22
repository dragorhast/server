from enum import Enum
from typing import Type

from marshmallow import Schema, fields, validates_schema, ValidationError

from server.serializer.fields import EnumField


class JSendStatus(Enum):
    """An Enum to quantify the JSend status states."""

    SUCCESS = "success"
    """Everything went as expected."""

    FAIL = "fail"
    """There was a user error with the request, or supplied data."""

    ERROR = "error"
    """There was a system error with the request."""


class JSendSchema(Schema):
    status = EnumField(JSendStatus, required=True)
    data = fields.Field()
    message = fields.String()
    code = fields.Integer()

    @validates_schema
    def ensure_fields(self, data):
        """Ensures the required fields are available."""
        if data["status"] == JSendStatus.SUCCESS or data["status"] == JSendStatus.FAIL:
            if "data" not in data:
                raise ValidationError("When status is %s, the data field must be populated.",
                                      data["status"])
        elif data["status"] == JSendStatus.ERROR:
            if "message" not in data:
                raise ValidationError(
                    "When the status is %s, the message fields must be populated.", data["status"])

    @staticmethod
    def of(data_type: Type):
        """Creates a subclass of JSendSchema of a specific data type."""

        class TypedJSendSchema(JSendSchema):
            data = fields.Nested(data_type)

        return TypedJSendSchema()
