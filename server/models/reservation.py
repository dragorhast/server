from enum import Enum

from tortoise import Model, fields

from server.models.fields import EnumField


class ReservationOutcome(str, Enum):
    CLAIMED = "claimed"
    CANCELLED = "canceled"
    EXPIRED = "expired"


class Reservation(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="reservations")
    pickup_point = fields.ForeignKeyField("models.PickupPoint", related_name="reservations")
    claimed_rental = fields.ForeignKeyField("models.Rental", related_name="rentals", null=True)
    made_at = fields.DatetimeField(auto_now_add=True)
    reserved_for = fields.DatetimeField()
    ended_at = fields.DatetimeField(null=True)
    outcome = EnumField(ReservationOutcome, null=True)

    def serialize(self, router):
        data = {
            "user_id": self.user_id,
            "user_url": router["user"].url_for(id=str(self.user_id)).path,
            "pickup_id": self.pickup_point_id,
            "pickup_url": router["pickup"].url_for(id=str(self.pickup_point_id)).path,
            "made_at": self.made_at,
            "reserved_for": self.reserved_for,
        }

        if self.claimed_rental_id is not None:
            data["rental_id"] = self.claimed_rental_id
            data["rental_url"] = router["rental"].url_for(id=str(self.claimed_rental_id)).path

        if self.ended_at is not None:
            data["ended_at"] = self.ended_at
            data["outcome"] = self.outcome

        return data
