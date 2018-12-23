from marshmallow import Schema
from marshmallow.fields import Boolean, Integer, Nested, String, Email, DateTime

from server.serializer.fields import BytesField


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


class RentalSchema(Schema):
    id = Integer()
    user = Nested(UserSchema(), required=True)
    bike = Nested(BikeSchema(), required=True)
    start = DateTime(required=True)
    end = DateTime()
