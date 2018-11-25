import weakref
from typing import Optional, Callable

from aiohttp.web_ws import WebSocketResponse
from attr import dataclass


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
    pub: bytes
    _socket: Optional[Callable[[], Optional[WebSocketResponse]]] = None
    """
    A weak reference to the websocket. Weak references, when called,
    return the object they are supposed to reference, or None if it
    has been deleted.
    """

    locked: bool = True

    def serialize(self):
        return {
            "id": self.bid,
            "pub": self.pub.hex(),
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

    async def set_locked(self, locked):
        await self._socket.send_str("lock" if locked else "unlock")
        self.locked = locked
