"""
Bike
-------------------------

Represents a bike on the server. The bike has a number of operations on
it that proxy commands on the real world bike. This requires that an open
socket to a bike is open before these operations are handled. To handle this,
the server maintains a :class:`~server.service.bike_connection_Manager.BikeConnectionManager`
which facilitates bike location updates and remote procedure calls on all
connected bikes.
"""
from enum import Enum
from typing import Dict, Any

from shapely.geometry import mapping
from tortoise import Model, fields

from server.models.fields import EnumField
from server.models.util import BikeType
from server.serializer.geojson import GeoJSONType


class BikeStatus(Enum):
    AVAILABLE = "available",
    BROKEN = "broken",
    OUT_OF_SERVICE = "out_of_service"
    RENTED = "rented",
    DISCONNECTED = "disconnected"

    @classmethod
    def get_status(cls, available, rented, in_service, broken):
        if not in_service:
            return cls.OUT_OF_SERVICE
        elif broken:
            return cls.BROKEN
        elif rented:
            return cls.RENTED
        elif available:
            return cls.AVAILABLE
        else:
            return cls.DISCONNECTED



class Bike(Model):
    id = fields.IntField(pk=True)
    public_key_hex: str = fields.CharField(max_length=64, unique=True)
    type = EnumField(enum_type=BikeType, default=BikeType.ROAD)

    def serialize(
        self, bike_connection_manager, rental_manager,
        reservation_manager, include_location=False
    ) -> Dict[str, Any]:
        """
        Serializes the bike into a format that can be turned into JSON.

        :param include_location: Whether to force include the location, ignoring whether it is available (PRIVACY WARNING)
        :return: A dictionary.
        """
        connected = bike_connection_manager.is_connected(self)
        rented = not rental_manager.is_available(self, reservation_manager)
        available = connected and not rented
        broken = False  # todo implement
        in_service = False  # todo implement

        status = BikeStatus.get_status(available, rented, in_service, broken)

        data = {
            "identifier": self.identifier,
            "public_key": self.public_key,
            "connected": connected,
            "rented": rented,
            "available": available,
            "broken": broken,
            "in_service": in_service,
            "status": status
        }

        if connected:
            data["battery"] = bike_connection_manager.battery_level(self.id)
            data["locked"] = bike_connection_manager.is_locked(self.id)

        recent_location = bike_connection_manager.most_recent_location(self)
        if recent_location is not None and (data["available"] or include_location):
            location, time, pickup_point = recent_location

            data["current_location"] = {
                "type": GeoJSONType.FEATURE,
                "geometry": mapping(location)
            }

            if pickup_point is not None:
                data["current_location"]["properties"] = {"pickup_point": pickup_point.name}

        return data

    @property
    def public_key(self) -> bytes:
        """The public key bytes."""
        return bytes.fromhex(self.public_key_hex)

    @property
    def identifier(self) -> str:
        """The 6 character bike identifier."""
        return self.public_key_hex[:6]
