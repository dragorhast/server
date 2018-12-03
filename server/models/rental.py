from dataclasses import dataclass

from server.models.bike import Bike
from server.models.user import User


@dataclass
class Rental:
    bike: Bike
    user: User
