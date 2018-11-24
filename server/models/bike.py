from typing import Optional

from aiohttp.web_ws import WebSocketResponse
from attr import dataclass


@dataclass
class Bike:

    bid: int
    pub: bytes
    socket: Optional[WebSocketResponse] = None

    def serialize(self):
        return {
            "id": self.bid,
            "pub": self.pub.hex()
        }
