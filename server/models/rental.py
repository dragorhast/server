"""
Contains the various
"""

from datetime import datetime

from tortoise import Model, fields

from server.models.util import RentalUpdateType
from server.models.fields import EnumField
from server.serializer import RentalSchema


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

    def serialize(self):
        schema = RentalSchema()

        rental_data = {
            "user_id": self.user_id,
            "bike_id": self.bike_id,
            "price": self.price
        }

        return schema.dump(rental_data)
