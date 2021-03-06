"""
Model Serializers
-----------------

Defines serializers for the various models in the system.
"""

from marshmallow import Schema, validates_schema, ValidationError
from marshmallow.fields import Integer, Boolean, String, Email, Nested, DateTime, Float, Url, List

from server.models.bike import CalculatedBikeStatus
from server.models.issue import IssueStatus
from server.models.reservation import ReservationOutcome
from server.models.util import RentalUpdateType
from server.serializer.geojson import GeoJSON, GeoJSONType
from .fields import BytesField, EnumField


class BikeSchema(Schema):
    public_key = BytesField()
    identifier = BytesField(required=True, as_string=True, max_length=6)
    available = Boolean(required=True)
    connected = Boolean()
    rented = Boolean()
    broken = Boolean()
    in_circulation = Boolean()
    status = EnumField(CalculatedBikeStatus, default=CalculatedBikeStatus.AVAILABLE)
    battery = Float()
    locked = Boolean()
    current_location = Nested(GeoJSON(GeoJSONType.FEATURE))
    open_issues = Nested('IssueSchema', many=True, exclude=('bike',))

    @validates_schema
    def assert_current_location_on_available_bikes(self, data, **kwargs):
        """Assert that anything marked available has a current location."""
        if "available" in data and data["available"]:
            if "current_location" not in data:
                raise ValidationError("If the bike is available, the current location must also be included.")


class UserSchema(Schema):
    """The schema corresponding to the :class:`~server.models.user.User` model."""

    id = Integer()
    firebase_id = String(required=True)
    stripe_id = String(allow_none=True)
    first = String(required=True)
    email = Email(required=True)

    @validates_schema
    def assert_strip_id_valid(self, data, **kwargs):
        if "stripe_id" not in data or data["stripe_id"] is None:
            return True

        return data["stripe_id"].startswith("cus_")


class RentalUpdateSchema(Schema):
    type = EnumField(RentalUpdateType, required=True)
    time = DateTime(required=True)


class RentalSchema(Schema):
    id = Integer(required=True)

    user = Nested(UserSchema())
    user_id = Integer()
    user_url = Url(relative=True)

    bike = Nested(BikeSchema())
    bike_identifier = BytesField(as_string=True)
    bike_url = Url(relative=True)

    events = Nested(RentalUpdateSchema(), many=True)
    start_time = DateTime(required=True)
    end_time = DateTime()
    cancel_time = DateTime()

    is_active = Boolean(required=True)
    price = Float()
    distance = Float()

    @validates_schema
    def assert_end_time_with_price(self, data, **kwargs):
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
    def assert_url_included_with_foreign_key(self, data, **kwargs):
        """
        Asserts that when a user_id or bike_id is sent that a user_url or bike_url is sent with it.
        """
        if "user_id" in data and "user_url" not in data:
            raise ValidationError("User ID was included, but User URL was not.")
        if "bike_id" in data and "bike_url" not in data:
            raise ValidationError("Bike ID was included, but Bike URL was not.")


class CurrentRentalSchema(RentalSchema):
    start_location = Nested(GeoJSON(GeoJSONType.FEATURE), allow_none=True)
    current_location = Nested(GeoJSON(GeoJSONType.FEATURE), allow_none=True)
    estimated_price = Float()


class LatLong(Schema):
    latitude = Float()
    longitude = Float()


class PickupPointData(Schema):
    id = Integer()
    name = String(required=True)
    center = List(Float())
    shortage_count = Integer()
    shortage_date = DateTime()

    free_bikes = Integer()
    """The number of bikes that aren't currently reserved."""


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
    bike_identifier = BytesField(as_string=True, allow_none=True)
    bike_url = Url(relative=True, allow_none=True)

    opened_at = DateTime()
    closed_at = DateTime()
    description = String(required=True)
    resolution = String(allow_none=True)
    status = EnumField(IssueStatus, default=IssueStatus.OPEN)

    @validates_schema
    def assert_url_included_with_foreign_key(self, data, **kwargs):
        """
        Asserts that when a user_id or bike_id is sent that a user_url or bike_url is sent with it.
        """
        if "user_id" in data and "user_url" not in data:
            raise ValidationError("User ID was included, but User URL was not.")
        if "bike_id" in data and "bike_url" not in data:
            raise ValidationError("Bike ID was included, but Bike URL was not.")


class CreateReservationSchema(Schema):
    reserved_for = DateTime(required=True)


class ReservationSchema(CreateReservationSchema):
    id = Integer()

    made_at = DateTime()
    ended_at = DateTime()
    status = EnumField(ReservationOutcome, default=ReservationOutcome.OPEN)

    user = Nested(UserSchema())
    user_id = Integer()
    user_url = Url(relative=True)

    pickup = Nested(PickupPointSchema())
    pickup_id = Integer()
    pickup_url = Url(relative=True)

    rental = Nested(RentalSchema())
    rental_io = Integer()
    rental_url = Url(relative=True)


class CurrentReservationSchema(ReservationSchema):
    url = Url(relative=True, required=True)
