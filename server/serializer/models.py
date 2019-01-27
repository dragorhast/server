"""
Model Serializers
-----------------

Defines serializers for the various models in the system.
"""

from marshmallow import Schema, validates_schema, ValidationError
from marshmallow.fields import Integer, Boolean, String, Email, Nested, DateTime, Float, Url

from server.models.util import RentalUpdateType
from server.serializer.geojson import GeoJSON, GeoJSONType
from .fields import BytesField, EnumField


class BikeSchema(Schema):
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
    user_id = Integer()
    user_url = Url(relative=True)

    bike = Nested(BikeSchema())
    bike_id = Integer()
    bike_url = Url(relative=True)

    events = Nested(RentalUpdateSchema(), many=True)
    start_time = DateTime(required=True)
    end_time = DateTime()

    is_active = Boolean(required=True)
    estimated_price = Float()
    price = Float()
    distance = Float()

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

    @validates_schema
    def assert_url_included_with_foreign_key(self, data):
        """
        Asserts that when a user_id or bike_id is sent that a user_url or bike_url is sent with it.
        """
        if "user_id" in data and "user_url" not in data:
            raise ValidationError("User ID was included, but User URL was not.")
        if "bike_id" in data and "bike_url" not in data:
            raise ValidationError("Bike ID was included, but Bike URL was not.")


class CurrentRentalSchema(RentalSchema):
    start_location = Nested(GeoJSON(GeoJSONType.FEATURE))
    current_location = Nested(GeoJSON(GeoJSONType.FEATURE))


class PickupPointData(Schema):
    id = Integer()
    name = String(required=True)
    bikes = BikeSchema(many=True)


class PickupPointSchema(GeoJSON):

    def __init__(self, *args, **kwargs):
        super().__init__(GeoJSONType.FEATURE, *args, **kwargs)

    properties = Nested(PickupPointData())


class IssueSchema(Schema):
    id = Integer()

    user = Nested(UserSchema())
    user_id = Integer()
    user_url = Url(relative=True)

    bike = Nested(BikeSchema(), allow_none=True)
    bike_id = Integer(allow_none=True)
    bike_url = Url(relative=True, allow_none=True)

    time = DateTime()
    description = String(required=True)

    @validates_schema
    def assert_url_included_with_foreign_key(self, data):
        """
        Asserts that when a user_id or bike_id is sent that a user_url or bike_url is sent with it.
        """
        if "user_id" in data and "user_url" not in data:
            raise ValidationError("User ID was included, but User URL was not.")
        if "bike_id" in data and "bike_url" not in data:
            raise ValidationError("Bike ID was included, but Bike URL was not.")
