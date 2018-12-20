from datetime import datetime, timedelta
from enum import Enum

from tortoise import Model, fields


class RentalUpdate(Model):
    """A rental update."""

    id = fields.IntField(pk=True)

    user = fields.ForeignKeyField(model_name="models.User")
    bike = fields.ForeignKeyField(model_name="models.Bike")
    type = fields.IntField()
    time: datetime = fields.DatetimeField(auto_now_add=True)


class RentalUpdateType(Enum):

    RENT = 0
    RETURN = 1

