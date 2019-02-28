from enum import Enum
from typing import Union, Dict, Optional

from shapely.geometry import mapping
from tortoise import Model

from server.serializer import GeoJSONType


class BikeType(str, Enum):
    """We subclass string to make json serialization work."""
    ROAD = "road"


class RentalUpdateType(str, Enum):
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


def get_serialized_location_for_bike(bike, bike_connection_manager) -> Optional[Dict]:
    """Gets the serialized location for a bike."""

    recent_location = bike_connection_manager.most_recent_location(bike)
    if recent_location is None:
        return None

    location, time, pickup_point = recent_location

    serialized_location = {
        "type": GeoJSONType.FEATURE,
        "geometry": mapping(location),
        "properties": {
            "pickup_point": pickup_point.serialize()
        }
    }

    return serialized_location


class BikeUpdateType(str, Enum):
    OUT_OF_CIRCULATION = "out_of_circulation"
    SERVICED = "serviced"
    IN_CIRCULATION = "in_circulation"
