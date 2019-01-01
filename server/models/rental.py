"""
Rental
---------------------------

Contains the various
"""

from datetime import datetime
from typing import Dict, Any

from tortoise import Model, fields

from server.models.fields import EnumField
from server.models.util import RentalUpdateType


class RentalUpdate(Model):
    id = fields.IntField(pk=True)
    rental = fields.ForeignKeyField(model_name="models.Rental", related_name="updates")
    type = EnumField(RentalUpdateType)
    time: datetime = fields.DatetimeField(auto_now_add=True)


class Rental(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField(model_name="models.User", related_name="rentals")
    bike = fields.ForeignKeyField(model_name="models.Bike", related_name="rentals")
    price = fields.FloatField(null=True)

    @property
    def start_date(self):
        return self.updates[0].time

    @property
    def end_date(self):
        last_update: RentalUpdate = self.updates[-1]
        return last_update.time if last_update.type == RentalUpdateType.RETURN else None

    async def serialize(self, rental_manager) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "bike_id": self.bike_id,
            "start_time": self.start_date,
        }

        if self.end_date is not None:
            data["end_time"] = self.end_date
            data["price"] = self.price
        else:
            data["estimated_price"] = await rental_manager.get_price_estimate(self)

        return data
