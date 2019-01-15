"""
Model Serializers
-----------------

Defines serializers for the various models in the system.
"""

from marshmallow import Schema, validates_schema, ValidationError
from marshmallow.fields import Integer, Boolean, String, Email, Nested, DateTime, Float

from server.models.util import RentalUpdateType
from .fields import BytesField, EnumField


class BikeSchema(Schema):
    id = Integer()
    public_key = BytesField(required=True)
    connected = Boolean()
    locked = Boolean()


class UserSchema(Schema):
    """The schema corresponding to the :class:`~server.models.user.User` model."""

    id = Integer()
    firebase_id = BytesField(required=True)
    first = String(required=True)
    email = Email(required=True)


class RentalUpdateSchema(Schema):
    type = EnumField(RentalUpdateType, required=True)
    time = DateTime(required=True)


class RentalSchema(Schema):
    id = Integer(required=True)
    user = Nested(UserSchema())
    user_id = Integer(required=True)
    bike = Nested(BikeSchema())
    bike_id = Integer(required=True)
    events = Nested(RentalUpdateSchema(), many=True)
    start_time = DateTime(required=True)
    end_time = DateTime()
    is_active = Boolean(required=True)
    estimated_price = Float()
    price = Float()

    @validates_schema
    def assert_end_time_with_price(self, data):
        """
        Asserts that when a rental is complete both the price and end time are included.
        """
        if "price" in data and "end_time" not in data:
            raise ValidationError("If the price is included, you must also include the end time.")
        elif "price" not in data and "end_time" in data:
            raise ValidationError("If the end time is included, you must also include the price.")
        if "price" in data and "estimated_price" in data:
            raise ValidationError("Rental should have one of either price or estimated_price.")
