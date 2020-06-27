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
from typing import Dict, Any, List

from tortoise import Model, fields

from server.models.fields import EnumField
from server.models.util import BikeType, BikeUpdateType, get_serialized_location_for_bike


class CalculatedBikeStatus(str, Enum):
    """
    Represents the possible calculated states of a bike.
    """

    AVAILABLE = "available",
    BROKEN = "broken",
    OUT_OF_CIRCULATION = "out_of_circulation"
    RENTED = "rented",
    DISCONNECTED = "disconnected"

    @classmethod
    def get(cls, available, rented, in_circulation, broken):
        if not in_circulation:
            return cls.OUT_OF_CIRCULATION
        elif broken:
            return cls.BROKEN
        elif rented:
            return cls.RENTED
        elif available:
            return cls.AVAILABLE
        else:
            return cls.DISCONNECTED


class BikeStateUpdate(Model):
    id = fields.IntField(pk=True)
    bike = fields.ForeignKeyField("models.Bike", related_name="state_updates")
    time = fields.DatetimeField(auto_now_add=True)
    state = EnumField(BikeUpdateType)


class Bike(Model):
    id = fields.IntField(pk=True)
    public_key_hex: str = fields.CharField(max_length=64, unique=True)
    type = EnumField(enum_type=BikeType, default=BikeType.ROAD)

    def serialize(
        self, bike_connection_manager, rental_manager,
        reservation_manager, *, include_location=False, issues: List = None
    ) -> Dict[str, Any]:
        """
        Serializes the bike into a format that can be turned into JSON.

        :param include_location: Whether to force include the location, ignoring whether it is available (PRIVACY WARNING)
        :param issues: The open issues for the given bike.
        :return: A dictionary.
        """
        connected = bike_connection_manager.is_connected(self)
        rented = not rental_manager.is_available(self, reservation_manager)
        available = connected and not rented
        broken = self.broken
        in_circulation = self.in_circulation

        status = CalculatedBikeStatus.get(available, rented, in_circulation, broken)

        data = {
            "public_key": self.public_key,
            "identifier": self.identifier,
            "available": available,
            "connected": connected,
            "rented": rented,
            "broken": broken,
            "in_circulation": in_circulation,
            "status": status
        }

        if isinstance(issues, list):
            data["issues"] = issues

        if connected:
            data["battery"] = bike_connection_manager.battery_level(self.id)
            data["locked"] = bike_connection_manager.is_locked(self.id)

        if data["available"] or include_location:
            data["current_location"] = get_serialized_location_for_bike(self, bike_connection_manager,
                                                                        reservation_manager)

        return data

    @property
    def public_key(self) -> bytes:
        """The public key bytes."""
        return bytes.fromhex(self.public_key_hex)

    @property
    def identifier(self) -> str:
        """The 6 character bike identifier."""
        return self.public_key_hex[:6]

    @property
    def in_circulation(self) -> bool:
        for update in reversed(self.state_updates):
            if update.state in (BikeUpdateType.IN_CIRCULATION, BikeUpdateType.OUT_OF_CIRCULATION):
                return update.state is BikeUpdateType.IN_CIRCULATION

        return False

    @property
    def broken(self) -> bool:
        return len(self.issues) > 0

    def __str__(self):
        return f"[{self.type}] {self.identifier}"
