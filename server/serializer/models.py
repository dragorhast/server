"""
Defines serializers for the various models in the system.
"""

from marshmallow import Schema
from marshmallow.fields import Integer, Boolean, String, Email, Nested, DateTime

from server.models.util import RentalUpdateType
from .fields import BytesField, EnumField


class BikeSchema(Schema):
    id = Integer()
    public_key = BytesField(required=True)
    connected = Boolean()
    locked = Boolean()


class UserSchema(Schema):
    id = Integer()
    firebase_id = BytesField(required=True)
    first = String()
    email = Email()


class RentalUpdateSchema(Schema):
    type = EnumField(RentalUpdateType, required=True)
    time = DateTime(required=True)


class RentalSchema(Schema):
    id = Integer()
    user = Nested(UserSchema(), required=True)
    bike = Nested(BikeSchema(), required=True)
    events = Nested(RentalUpdateSchema(), many=True, required=True)
