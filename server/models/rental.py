"""
Rental
---------------------------

Contains the various
"""

from datetime import datetime
from typing import Dict, Any, Optional

from geopy import Point
from shapely.geometry import mapping
from tortoise import Model, fields

from server.models.fields import EnumField
from server.models.util import RentalUpdateType, get_serialized_location_for_bike
from server.serializer.geojson import GeoJSONType


class RentalUpdate(Model):
    id = fields.IntField(pk=True)
    rental = fields.ForeignKeyField(model_name="models.Rental", related_name="updates")
    type = EnumField(RentalUpdateType)
    time: datetime = fields.DatetimeField(auto_now_add=True)


class Rental(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField(model_name="models.User", related_name="rentals")
    bike = fields.ForeignKeyField(model_name="models.Bike", related_name="rentals")

    price = fields.IntField(null=True)
    """The price of the rental (in pennies)."""

    @property
    def start_time(self) -> datetime:
        return self.updates[0].time

    @property
    def end_time(self) -> Optional[datetime]:
        last_update: RentalUpdate = self.updates[-1]
        return last_update.time if last_update.type == RentalUpdateType.RETURN else None

    @property
    def cancel_time(self) -> Optional[datetime]:
        last_update: RentalUpdate = self.updates[-1]
        return last_update.time if last_update.type == RentalUpdateType.CANCEL else None

    @property
    def outcome(self) -> Optional[str]:
        last_update: RentalUpdate = self.updates[-1].type
        if last_update is RentalUpdateType.CANCEL:
            return "canceled"
        elif last_update is RentalUpdateType.RETURN:
            return "returned"
        else:
            return None

    async def serialize(self, rental_manager, bike_connection_manager, router=None, *,
                        distance: float = None,
                        start_location: Point = None,
                        current_location: Point = None
                        ) -> Dict[str, Any]:
        """
        .. todo:: make synchronous (we should be able to safely serialize without worrying about network or db)
            or, alternatively, only include price estimate on single requests
        """
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "bike_identifier": self.bike.identifier,
            "start_time": self.start_time,
            "is_active": rental_manager.is_active(self.id)
        }

        if router is not None:
            data["bike_url"] = router["bike"].url_for(identifier=str(self.bike.identifier)).path
            data["user_url"] = router["user"].url_for(id=str(self.user_id)).path

        if self.outcome is not None:
            if self.end_time is not None:
                data["end_time"] = self.end_time
                data["price"] = self.price
            elif self.cancel_time is not None:
                data["cancel_time"] = self.cancel_time
            else:
                raise Exception("Bad State")
        else:
            data["estimated_price"] = await rental_manager.get_price_estimate(self)

        if distance:
            data["distance"] = distance
        if start_location:
            data["start_location"] = {
                "type": GeoJSONType.FEATURE,
                "geometry": mapping(start_location)
            }

        if current_location:
            data["current_location"] = get_serialized_location_for_bike(self.bike, bike_connection_manager)

        return data
