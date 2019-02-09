import random
from asyncio import sleep
from datetime import timedelta

from aiohttp.web_ws import WebSocketResponse
from marshmallow import ValidationError
from nacl.signing import SigningKey, SignedMessage

from fakebike import logger
from server.serializer.json_rpc import JsonRPCRequest, JsonRPCResponse


class Bike:
    bid: int
    seed: bytes
    locked: bool

    def __init__(self, bid, seed, locked=True):
        self.bid = bid
        self.seed = seed
        self.signing_key = SigningKey(seed)
        self.locked = locked
        self.commands = {
            "lock": self.lock,
            "unlock": self.unlock,
        }
        self.socket: WebSocketResponse = None
        self.battery = random.randint(0, 100)

    @property
    def public_key(self):
        return self.signing_key.verify_key

    def sign(self, data) -> SignedMessage:
        return self.signing_key.sign(data)

    async def lock(self, request_id):
        self.locked = True
        await self.socket.send_json(JsonRPCResponse().dump({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": True
        }))

    async def unlock(self, request_id):
        self.locked = False
        await self.socket.send_json(JsonRPCResponse().dump({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": False
        }))

    async def handle_request(self, data):
        try:
            valid_data = JsonRPCRequest().load(data)
        except ValidationError as e:
            logger.error(e)
            return
        else:
            if valid_data["method"] in self.commands:
                await self.commands[valid_data["method"]](valid_data["id"])

    async def handle_response(self, data):
        try:
            valid_data = JsonRPCResponse().load(data)
        except ValidationError:
            return
        else:
            pass

    async def update_loop(self, delta: timedelta):
        while True:
            if self.socket is not None and not self.socket.closed:
                await self.socket.send_json({
                    "jsonrpc": "2.0",
                    "method": "location_update",
                    "params": {
                        "lat": 55.912136271818646,
                        "long": -3.3224467464697436,
                        "bat": self.battery
                    }

                })
                logger.info(f"Bike {self.bid} sent location and battery {self.battery}")
            await sleep(delta.total_seconds())
