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

from typing import Dict, Any

from tortoise import Model, fields

from server.models.fields import EnumField
from server.models.util import BikeType


class Bike(Model):

    id = fields.IntField(pk=True)
    public_key_hex: str = fields.CharField(max_length=64, unique=True)
    type = EnumField(enum_type=BikeType, default=BikeType.ROAD)

    def serialize(self, bike_connection_manager) -> Dict[str, Any]:
        """
        Serializes the bike into a format that can be turned into JSON.

        :return: A dictionary.
        """
        return {
            "id": self.id,
            "public_key": self.public_key,
            "connected": bike_connection_manager.is_connected(self),
            "locked": False
        }

    @property
    def public_key(self) -> bytes:
        """The public key bytes."""
        return bytes.fromhex(self.public_key_hex)

    @property
    def identifier(self) -> str:
        """The 6 character bike identifier."""
        return self.public_key_hex[:6]
