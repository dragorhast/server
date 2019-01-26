from enum import Enum
from typing import Union

from tortoise import Model


class BikeType(Enum):
    ROAD = "road"


class RentalUpdateType(Enum):
    RENT = "rent"
    RETURN = "return"
    LOCK = "lock"
    UNLOCK = "unlock"
    CANCEL = "cancel"

    @staticmethod
    def terminating_types():
        """The update types that result in the end of the rental."""
        return RentalUpdateType.RETURN, RentalUpdateType.CANCEL


def resolve_id(target: Union[Model, int]):
    if isinstance(target, Model):
        return target.id
    elif isinstance(target, int):
        return target
    else:
        raise TypeError(f"Target {target} is neither a Model or an int.")
