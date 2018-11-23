from asyncio import get_event_loop

import aiohttp
from aiohttp import ClientSession
from nacl.encoding import RawEncoder, HexEncoder
from nacl.signing import SigningKey

seed = bytes.fromhex("d09b31fc1bc4c05c8844148f06b0c218ac8fc3f1dcba0d622320b4284d67cc55")
"""This seed must be kept secret, and is used to verify identity."""

signing_key = SigningKey(seed)
print(f"Public key: {signing_key.verify_key.encode(HexEncoder).decode()}")

LOCKED = True
URL = "http://localhost:8080/api/v1/bikes/connect"


async def authenticate_session():
    """
    Posts the public key to the server, and
    returns the signing key required to start
    the session.
    """

    print(f"Initializing connection with {URL}")

    async with ClientSession() as session:

        # get the challenge
        async with session.post(URL, data=signing_key.verify_key.encode(RawEncoder)) as resp:
            if resp.status != 200 and resp.reason == "Identity not recognized.":
                print("Public key not on server")
                exit(1)
            challenge = await resp.read()

        signed_challenge = signing_key.sign(challenge)

        async with session.ws_connect(URL) as ws:
            # send signature
            await ws.send_bytes(signed_challenge)

            # handle messages
            async for msg in ws:
                print(msg.message)
                if msg.type == aiohttp.WSMsgType.TEXT:
                    if msg.data == 'close cmd':
                        await ws.close()
                        break
                    else:
                        await ws.send_str(msg.data + '/answer')
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break


loop = get_event_loop()
loop.run_until_complete(authenticate_session())
