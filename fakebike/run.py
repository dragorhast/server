from asyncio import get_event_loop, sleep
from datetime import timedelta

import aiohttp
from aiobreaker import CircuitBreaker, CircuitBreakerError
from aiohttp import ClientSession, ClientConnectorError
from nacl.encoding import RawEncoder

from fakebike import logger
from fakebike.bike import Bike

bike = Bike(bytes.fromhex("d09b31fc1bc4c05c8844148f06b0c218ac8fc3f1dcba0d622320b4284d67cc55"))
URL = "http://localhost:8080/api/v1/bikes/connect"


class AuthException(Exception):
    """Raised when there is an auth problem."""
    pass


ServerBreaker = CircuitBreaker(fail_max=10, timeout_duration=timedelta(seconds=30))
"""If a connection is dropped, try 10 times then once every 30 seconds."""


@ServerBreaker
async def get_challenge(session, public_key):
    """
    Gets the challenge from the server.

    :return: The challenge bytes
    :raises AuthError:
    """
    async with session.post(URL, data=public_key.encode(RawEncoder)) as resp:
        if resp.status != 200 and resp.reason == "Identity not recognized.":
            raise AuthException("Public key not on server")
        return await resp.read()


@ServerBreaker
async def start_handler(session, signed_challenge):
    """
    Opens an authenticated web socket session with the server.
    :return: None
    """
    async with session.ws_connect(URL) as ws:
        # send signature
        await ws.send_bytes(signed_challenge)
        logger.info(f"Connection established")

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


async def start_session():
    """
    Posts the public key to the server, and
    returns the signing key required to start
    the session.
    """
    logger.info(f"Initializing connection with {URL}")

    async with ClientSession() as session:
        while True:
            try:
                signed_challenge = bike.sign(await get_challenge(session, bike.public_key))
                await start_handler(session, signed_challenge)
            except AuthException as e:
                logger.error("%s, quitting...", e)
                return
            except ClientConnectorError as e:
                logger.error("Connection lost, retrying..")
                await sleep(1)
                continue
            except CircuitBreakerError as e:
                logger.debug("Circuit Breaker open after too many retrys")
                await sleep(10)
                continue


loop = get_event_loop()
loop.run_until_complete(start_session())
