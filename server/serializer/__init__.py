from marshmallow import Schema
from marshmallow.fields import Boolean, Integer

from server.serializer.fields import BytesField


class BikeSchema(Schema):
    id = Integer()
    public_key = BytesField(required=True)
    connected = Boolean()
