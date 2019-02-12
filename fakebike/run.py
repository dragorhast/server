"""
Creates and registers multiple fake bikes with the server. Connections are automatically retried when dropped.

.. note:: The public keys must be registered with the server.
"""
from asyncio import get_event_loop, sleep, gather
from json import JSONDecodeError

import aiohttp
from aiobreaker import CircuitBreaker, CircuitBreakerError
from aiohttp import ClientSession, ClientConnectorError, WSMessage
from datetime import timedelta
from nacl.encoding import RawEncoder

from fakebike import logger
from fakebike.bike import Bike
from server.models.util import BikeType
from server.views.bikes import BikeRegisterSchema

bikes = {
    0: Bike(0, bytes.fromhex("d09b31fc1bc4c05c8844148f06b0c218ac8fc3f1dcba0d622320b4284d67cc55")),
    1: Bike(1, bytes.fromhex("1e163e14b5a7d6e8914489d76ed17a52d16aba49357f3eeef7f1d5a4dc3d57b5")),
    2: Bike(2, bytes.fromhex("4af429ad536e92d791ed3137c382b0ae48520867119654c8c10d8e81d9b65f0e")),
    3: Bike(3, bytes.fromhex("a68f921cab9631842f6c4d2e792fc163a978c47dbba685eb5b88b0fb54b23939"))
}

for bike in bikes.values():
    get_event_loop().create_task(bike.update_loop(timedelta(seconds=10)))

URL = "http://localhost:8080/api/v1/bikes"


class AuthError(Exception):
    """Raised when there is an auth problem."""
    pass


ServerBreaker = CircuitBreaker(fail_max=10, timeout_duration=timedelta(seconds=30))
"""If a connection is dropped, try 10 times then once every 30 seconds."""


@ServerBreaker
async def create_ticket(session, bike: Bike):
    """
    Gets the challenge from the server.

    :return: The challenge bytes
    :raises AuthError:
    """
    async with session.post(URL + "/connect", data=bike.public_key.encode(RawEncoder)) as resp:
        if resp.status != 200 and resp.reason == "Identity not recognized.":
            raise AuthError("public key not on server")
        return await resp.read()


@ServerBreaker
async def bike_handler(session, bike: Bike, signed_challenge: bytes):
    """
    Opens an authenticated web socket session with the server.

    :return: None
    """
    async with session.ws_connect(URL + "/connect") as socket:
        # send signature
        await socket.send_bytes(bike.public_key.encode(RawEncoder))
        await socket.send_bytes(signed_challenge)
        confirmation = await socket.receive_str()
        if "fail" in confirmation:
            raise AuthError(confirmation.split(":")[1])
        else:
            logger.info(f"Bike {bike.bid} established connection")
            await socket.send_json({"locked": bike.locked})
        bike.socket = socket
        # handle messages
        async for msg in socket:
            msg: WSMessage = msg
            logger.info("Message %s", msg)
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    data = msg.json()
                except JSONDecodeError:
                    continue
                else:
                    if "method" in data:
                        await bike.handle_request(data)
                    else:
                        await bike.handle_response(data)


@ServerBreaker
async def register_bike(session, bike: Bike, master_key: bytes):
    bike_register = {
        "public_key": bike.public_key.encode(RawEncoder),
        "type": BikeType.ROAD,
        "master_key": master_key
    }
    schema = BikeRegisterSchema()

    bike_serialized = schema.dump(bike_register)

    async with session.post(URL, json=bike_serialized) as resp:
        text = await resp.text()
        pass


async def start_session(bike: Bike):
    """
    Posts the public key to the server, and
    returns the signing key required to start
    the session.
    """
    logger.info(f"Bike {bike.bid} initializing connection with {URL}")

    async with ClientSession() as session:
        while True:
            try:
                challenge = await create_ticket(session, bike)
                signature = bike.sign(challenge).signature
                await bike_handler(session, bike, signature)
            except AuthError as e:
                if "public key not on server" in e.args:
                    await register_bike(session, bike, 0xdeadbeef.to_bytes(4, "big"))
                else:
                    logger.error(f"Bike {bike.bid} {e}, quitting...")
                    return
            except ClientConnectorError as e:
                logger.error("Connection lost, retrying..")
                await sleep(2)
                continue
            except CircuitBreakerError as e:
                logger.debug("Circuit Breaker open after too many retries")
                await sleep(10)
                continue


if __name__ == '__main__':
    loop = get_event_loop()
    loop.run_until_complete(gather(*[start_session(bike) for bike in bikes.values()]))
