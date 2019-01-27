"""
Bike
-------------------------

Represents a bike on the server. The bike has a number of operations on
it that proxy commands on the real world bike. This requires that an open
socket to a bike is open before these operations are handled. To do this,
make a connection with the bike, set the opened socket to the socket variable
on the bike itself.

For an example of this, see :class:`~server.views.bikes.BikeSocketView`.
"""

from typing import Optional, Callable, Dict, Any

from aiohttp.web_ws import WebSocketResponse
from tortoise import Model, fields

from server.models.fields import EnumField
from server.models.util import BikeType


class Bike(Model):
    """
    The main class for the bike.

    Uses a weak reference to its socket when connected to ensure that
    closed connections are inaccessible after closing. Weak references
    allow the garbage collector to delete the object even though there
    is still a reference to it. This stops potential leaks and minimizes
    chances of crashes due to writing to closed sockets.
    """

    id = fields.IntField(pk=True)
    public_key_hex: str = fields.CharField(max_length=64, unique=True)
    type = EnumField(enum_type=BikeType, default=BikeType.ROAD)

    locked: bool = True
    _socket: Callable[..., Optional[WebSocketResponse]] = lambda *args: None
    _public_key: bytes
    """
    A weak reference to the websocket. Weak references, when called,
    return the object they are supposed to reference, or None if it
    has been deleted. We set it to lambda None to emulate this behaviour.
    """

    def serialize(self, bike_connection_manager) -> Dict[str, Any]:
        """
        Serializes the bike into a format that can be turned into JSON.

        :return: A dictionary.
        """
        return {
            "id": self.id,
            "public_key": self.public_key,
            "connected": bike_connection_manager.is_connected(self),
            "locked": self.locked
        }

    @property
    def public_key(self):
        if hasattr(self, '_public_key'):
            return self._public_key

        self._public_key = bytes.fromhex(self.public_key_hex)
        return self._public_key
