"""
Represents a bike on the server. The bike has a number of operations on
it that proxy commands on the real world bike. This requires that an open
socket to a bike is open before these operations are handled. To do this,
make a connection with the bike, set the opened socket to the socket variable
on the bike itself.

For an example of this, see :class:`~server.views.bikes.BikeSocketView`.
"""

import weakref
from typing import Optional, Callable, Dict, Any

from aiohttp.web_ws import WebSocketResponse
from dataclasses import dataclass


@dataclass
class Bike:
    """
    The main class for the bike.

    Uses a weak reference to its socket when connected to ensure that
    closed connections are inaccessible after closing. Weak references
    allow the garbage collector to delete the object even though there
    is still a reference to it. This stops potential leaks and minimizes
    chances of crashes due to writing to closed sockets.
    """

    bid: int
    public_key: bytes
    _socket: Optional[Callable[[], Optional[WebSocketResponse]]] = None
    """
    A weak reference to the websocket. Weak references, when called,
    return the object they are supposed to reference, or None if it
    has been deleted.
    """

    locked: bool = True

    def serialize(self) -> Dict[str, Any]:
        """
        Serializes the bike into a format that can be turned into JSON.

        :return: A dictionary.
        """
        return {
            "id": self.bid,
            "pub": self.public_key.hex(),
            "connected": self._is_connected,
            "locked": self.locked
        }

    @property
    def _is_connected(self):
        """
        Checks if the bike has been assigned a weak reference
        to a socket and if the socket is still alive.
        """
        return self._socket is not None and self._socket() is not None

    def _set_socket(self, socket):
        self._socket = weakref.ref(socket)

    socket = property(None, _set_socket)
    """Assigns the server bike a socket over which it can communicate with the actual bike."""

    async def set_locked(self, locked: bool):
        """
        Locks or unlocks the bike.

        :param locked: The status to set the bike to.
        :return: None
        :raises ConnectionError: If the socket is not open.
        """
        if not self._is_connected:
            raise ConnectionError("No open socket.")
        await self._socket().send_str("lock" if locked else "unlock")
        self.locked = locked
