"""
Creates and registers multiple fake bikes with the server. Connections are automatically retried when dropped.

.. note:: The public keys must be registered with the server.
"""
import json
from asyncio import get_event_loop, sleep, gather
from datetime import timedelta

import aiohttp
from aiobreaker import CircuitBreaker, CircuitBreakerError
from aiohttp import ClientSession, ClientConnectorError
from nacl.encoding import RawEncoder

from fakebike import logger
from fakebike.bike import Bike

bikes = {
    0: Bike(0, bytes.fromhex("d09b31fc1bc4c05c8844148f06b0c218ac8fc3f1dcba0d622320b4284d67cc55"), locked=False),
    1: Bike(1, bytes.fromhex("1e163e14b5a7d6e8914489d76ed17a52d16aba49357f3eeef7f1d5a4dc3d57b5")),
    2: Bike(2, bytes.fromhex("4af429ad536e92d791ed3137c382b0ae48520867119654c8c10d8e81d9b65f0e"), locked=True),
    3: Bike(3, bytes.fromhex("a68f921cab9631842f6c4d2e792fc163a978c47dbba685eb5b88b0fb54b23939"), locked=True)
}

URL = "http://localhost:8080/api/v1/bikes/connect"


class AuthException(Exception):
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
    async with session.post(URL, data=bike.public_key.encode(RawEncoder)) as resp:
        if resp.status != 200 and resp.reason == "Identity not recognized.":
            raise AuthException("public key not on server")
        return await resp.read()


@ServerBreaker
async def bike_handler(session, bike: Bike, signed_challenge):
    """
    Opens an authenticated web socket session with the server.

    :return: None
    """
    async with session.ws_connect(URL) as ws:
        # send signature
        await ws.send_bytes(bike.public_key.encode(RawEncoder))
        await ws.send_bytes(signed_challenge)
        confirmation = await ws.receive_str()
        if "fail" in confirmation:
            raise AuthException(confirmation.split(":")[1])
        else:
            logger.info(f"Bike {bike.bid} established connection")
            await ws.send_json({"locked": bike.locked})

        # handle messages
        async for msg in ws:
            logger.info("Message %s", msg)
            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == 'close cmd':
                    await ws.close()
                    logger.info("closing connection")
                    break
                elif msg.data in bike.commands:
                    await bike.commands[msg.data](msg, ws)


async def start_session(bike):
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
            except AuthException as e:
                logger.error(f"Bike {bike.bid} {e}, quitting...")
                return
            except ClientConnectorError as e:
                logger.error("Connection lost, retrying..")
                await sleep(1)
                continue
            except CircuitBreakerError as e:
                logger.debug("Circuit Breaker open after too many retrys")
                await sleep(10)
                continue

if __name__ == '__main__':
    loop = get_event_loop()
    loop.run_until_complete(gather(*[start_session(bike) for bike in bikes.values()]))
