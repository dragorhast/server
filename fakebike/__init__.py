from asyncio import get_event_loop

import aiohttp
from aiohttp import ClientSession
from nacl.encoding import RawEncoder, HexEncoder
from nacl.signing import SigningKey


class Bike:
    seed: bytes
    locked: bool = False

    def __init__(self, seed):
        self.seed = seed
        self.signing_key = SigningKey(seed)
        self.commands = {
            "lock": self.lock,
            "unlock": self.unlock,
        }

    @property
    def public_key(self):
        return self.signing_key.verify_key

    def sign(self, data):
        return self.signing_key.sign(data)

    async def lock(self, msg, socket):
        self.locked = True
        await socket.send_str("locked")

    async def unlock(self, msg, socket):
        self.locked = False
        await socket.send_str("unlocked")


bike = Bike(bytes.fromhex("d09b31fc1bc4c05c8844148f06b0c218ac8fc3f1dcba0d622320b4284d67cc55"))
print(f"Public key: {bike.public_key.encode(HexEncoder).decode()}")
URL = "http://localhost:8080/api/v1/bikes/connect"


async def authenticate_session():
    """
    Posts the public key to the server, and
    returns the signing key required to start
    the session.
    """
    global LOCKED
    print(f"Initializing connection with {URL}")

    async with ClientSession() as session:

        # get the challenge
        async with session.post(URL, data=bike.public_key.encode(RawEncoder)) as resp:
            if resp.status != 200 and resp.reason == "Identity not recognized.":
                print("Public key not on server")
                exit(1)
            challenge = await resp.read()

        signed_challenge = bike.sign(challenge)

        async with session.ws_connect(URL) as ws:
            # send signature
            await ws.send_bytes(signed_challenge)

            # handle messages
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    if msg.data == 'close cmd':
                        await ws.close()
                        print("closing connection")
                        break
                    elif msg.data in bike.commands:
                        await bike.commands[msg.data](msg, ws)
                    else:
                        print(msg)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(msg)
                    print("connection error")
                    break


loop = get_event_loop()
loop.run_until_complete(authenticate_session())
