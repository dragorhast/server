"""
Represents a bike on the server. The bike has a number of operations on
it that proxy commands on the real world bike. This requires that an open
socket to a bike is open before these operations are handled. To do this,
make a connection with the bike, set the opened socket to the socket variable
on the bike itself.

For an example of this, see :class:`~server.views.bikes.BikeSocketView`.
"""

import weakref
from enum import Enum
from typing import Optional, Callable, Dict, Any

from aiohttp.web_ws import WebSocketResponse
from tortoise import Model, fields

from server.models.fields import EnumField
from server.serializer import BikeSchema


class BikeType(Enum):
    ROAD = "road"


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
    public_key_hex = fields.CharField(max_length=64)
    type = EnumField(enum_type=BikeType, default=BikeType.ROAD)

    locked: bool = True
    _socket: Callable[..., Optional[WebSocketResponse]] = lambda *args: None
    """
    A weak reference to the websocket. Weak references, when called,
    return the object they are supposed to reference, or None if it
    has been deleted. We set it to lambda None to emulate this behaviour.
    """

    def serialize(self) -> Dict[str, Any]:
        """
        Serializes the bike into a format that can be turned into JSON.

        :return: A dictionary.
        """
        schema = BikeSchema(exclude=("connected", "locked"))

        data = schema.dump({
            "id": self.id,
            "public_key": self.public_key,
            "connected": self._is_connected,
            "locked": self.locked
        })

        return data

    @property
    def public_key(self):
        if hasattr(self, '_public_key'):
            return self._public_key
        else:
            self._public_key = bytes.fromhex(self.public_key_hex)
            return self._public_key

    @property
    def _is_connected(self):
        """
        Checks if the bike has been assigned a weak reference
        to a socket and if the socket is still alive.
        """
        return self._socket() is not None

    def _set_socket(self, socket):
        self._socket = weakref.ref(socket)

    socket = property(None, _set_socket)
    """Assigns the server bike a socket over which it can communicate with the actual bike."""

    async def set_locked(self, locked: bool):
        """
        Locks or unlocks the bike.

        :param locked: The status to set the bike to.
        :raises ConnectionError: If the socket is not open.
        """
        socket = self._socket()

        if not self._is_connected or socket is None:
            raise ConnectionError("No open socket.")

        await socket.send_str("lock" if locked else "unlock")
        self.locked = locked
