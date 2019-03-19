"""
Creates and registers multiple fake bikes with the server. Connections are automatically retried when dropped.

.. note:: The public keys must be registered with the server.
"""
import asyncio
import threading
from asyncio import get_event_loop, sleep, gather
from datetime import timedelta
from json import JSONDecodeError

import aiohttp
from aiobreaker import CircuitBreaker, CircuitBreakerError
from aiohttp import ClientSession, ClientConnectorError
from nacl.encoding import RawEncoder
from shapely.geometry import Point

from fakebike import logger
from fakebike.bike import Bike
from server.models.util import BikeType
from server.views.bikes import BikeRegisterSchema

"""
mountbatten
POLYGON((-3.3223096196969664 55.91305998919741,-3.323613173278204 55.91247071281088,-3.3226261203607237 55.91179122994221,-3.3212581937631285 55.91234443813432,-3.3223096196969664 55.91305998919741))

oriam
POLYGON((-3.3155809236718596 55.91111010164862,-3.314272005672592 55.910208099000634,-3.3176301313592376 55.908891137454894,-3.3185528112603606 55.90979317073678,-3.3155809236718596 55.91111010164862))

union
POLYGON((-3.31811911873433 55.91151312626592,-3.3186877470454874 55.91127259677804,-3.31811911873433 55.91079754665614,-3.317550490423173 55.9110861853987,-3.31811911873433 55.91151312626592))
"""

END_EVENT = asyncio.Event()

bikes = {
    1: Bike(1, bytes.fromhex("1e163e14b5a7d6e8914489d76ed17a52d16aba49357f3eeef7f1d5a4dc3d57b5"), Point(-3.322935456835012, 55.912744071892135)),
    2: Bike(2, bytes.fromhex("4af429ad536e92d791ed3137c382b0ae48520867119654c8c10d8e81d9b65f0e"), Point(-3.323002512060384, 55.91272302628964)),
    3: Bike(3, bytes.fromhex("a68f921cab9631842f6c4d2e792fc163a978c47dbba685eb5b88b0fb54b23939"), Point(-3.3230186053144735, 55.91272152303189)),
    4: Bike(4, bytes.fromhex("8E006615D69E9B96F1894B93BF428E7AED58807258497DC365C6F5202FA8834C"), Point(-3.323056156240682, 55.91269446438228)),
    5: Bike(5, bytes.fromhex("AF06AFC6B91BB9AC3A80F203F90D27942D8B1BDC2EBA3AF0DB5CF762C6A375F3"), Point(-3.3229909611643507, 55.91224956614896)),
    6: Bike(6, bytes.fromhex("4E01949C8AD62CBEA1F4B52AEA1F804D615DFE679B691147FBE8A07AF4B272B6"), Point(-3.322058173835785, 55.91132757124132)),
    7: Bike(7, bytes.fromhex("85CE1168638A16D78A6B9F413574A8D1C77653196F9872428D62AB0B40B3B503"), Point(-3.32194015663913, 55.911231359164816)),
    8: Bike(8, bytes.fromhex("B7B49E778B9B32577C7825EFB0FB1CE2BEB93239E37FCEB89290EAE94147FD63"), Point(-3.3168040109826507, 55.910286273393886)),
}

for bike in bikes.values():
    get_event_loop().create_task(bike.update_loop(timedelta(seconds=10)))

URL = "https://api.tap2go.co.uk/api/v1/bikes"


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

    async def handle_messages(socket):
        async for msg in socket:
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

    async def handle_disconnect(socket):
        await END_EVENT.wait()
        logger.info("Closing socket")
        await socket.close()

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
        await asyncio.wait([handle_messages(socket), handle_disconnect(socket)])


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
        while not END_EVENT.is_set():
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


def websocket_handler(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(gather(*coroutines))


if __name__ == '__main__':
    coroutines = [start_session(bike) for bike in bikes.values()]
    loop = asyncio.get_event_loop()

    threading.Thread(target=websocket_handler, args=(loop,)).start()

    event = threading.Event()
    try:
        event.wait()
    except KeyboardInterrupt:
        END_EVENT.set()

