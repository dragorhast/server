from typing import Optional

from aiohttp.web_ws import WebSocketResponse
from attr import dataclass


@dataclass
class Bike:

    bid: int
    pub: bytes
    socket: Optional[WebSocketResponse] = None
    locked: bool = True

    def serialize(self):
        return {
            "id": self.bid,
            "pub": self.pub.hex(),
            "locked": self.locked
        }

    async def set_locked(self, locked):
        await self.socket.send_str("lock" if locked else "unlock")
        self.locked = locked


