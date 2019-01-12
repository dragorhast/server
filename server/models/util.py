from enum import Enum


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
