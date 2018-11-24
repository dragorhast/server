from asyncio import get_event_loop

import aiohttp
from aiohttp import ClientSession
from nacl.encoding import RawEncoder

from fakebike import logger
from fakebike.bike import Bike

bike = Bike(bytes.fromhex("d09b31fc1bc4c05c8844148f06b0c218ac8fc3f1dcba0d622320b4284d67cc55"))
URL = "http://localhost:8080/api/v1/bikes/connect"


class AuthException(Exception):
    """Raised when there is an auth problem."""
    pass


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
            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == 'close cmd':
                    await ws.close()
                    logger.info("closing connection")
                    break
                elif msg.data in bike.commands:
                    await bike.commands[msg.data](msg, ws)
                else:
                    print(msg)

            elif msg.type == aiohttp.WSMsgType.ERROR:
                print(msg)
                logger.info("connection error")
                break


async def start_session():
    """
    Posts the public key to the server, and
    returns the signing key required to start
    the session.
    """
    logger.info(f"Initializing connection with {URL}")

    async with ClientSession() as session:
        try:
            signed_challenge = bike.sign(await get_challenge(session, bike.public_key))
        except AuthException as e:
            print(e)
            exit(1)
        else:
            await start_handler(session, signed_challenge)


loop = get_event_loop()
loop.run_until_complete(start_session())
