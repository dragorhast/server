from datetime import datetime
from enum import Enum

from tortoise import Model, fields

from server.models.fields import EnumField


class RentalUpdateType(Enum):
    RENT = "rent"
    RETURN = "return"
    LOCK = "lock"
    UNLOCK = "unlock"
    CANCEL = "cancel"


class RentalUpdate(Model):
    """A rental update."""

    id = fields.IntField(pk=True)

    user = fields.ForeignKeyField(model_name="models.User")
    bike = fields.ForeignKeyField(model_name="models.Bike")
    type = EnumField(RentalUpdateType)
    time: datetime = fields.DatetimeField(auto_now_add=True)
