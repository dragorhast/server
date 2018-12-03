from dataclasses import dataclass

from server.models.bike import Bike
from server.models.user import User


@dataclass
class Rental:
    rid: int
    bike: Bike
    user: User

    def serialize(self):
        return {
            "id": self.rid,
            "bike": self.bike.serialize(),
            "user": self.user.serialize()
        }
