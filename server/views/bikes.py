"""
Handles all the bike CRUD
"""
from collections import namedtuple
from datetime import datetime

from nacl.exceptions import BadSignatureError
from typing import Tuple, Dict

from aiohttp import web, BasicAuth, WSMsgType
from nacl.encoding import HexEncoder, RawEncoder
from nacl.signing import VerifyKey
from nacl.utils import random

from server.store import Store
from server.views.base import BaseView

store = Store()


class BikesView(BaseView):
    """
    Gets the bikes, or adds a new bike.
    """
    url = "/bikes"
    cors_allowed = True

    async def get(self):
        return web.json_response(store.get_bikes())

    async def post(self):
        pass


class BikeView(BaseView):
    """
    Gets or updates a single bike.
    """
    url = "/bikes/{id:[0-9]+}"
    cors_allowed = True

    async def get(self):
        pass

    async def delete(self):
        pass

    async def patch(self):
        pass

    async def put(self):
        pass


BikeTicket = namedtuple('BikeTicket', ['pub_key', 'challenge', 'timestamp'])


class BikeSocketView(BaseView):
    """
    Provides an endpoint for the server to communicate with the bikes.

    The bike posts to the url with their public key. A challenge is returned
    to the bike and signed. This ephemeral key is then sent to the server
    when setting up the connection. If the signed key is valid, the connection
    is accepted.

    Keys are 128 bit Ed25519 keys, for digital signatures.
    """

    url = "/bikes/connect"

    current_challenges: Dict[str, BikeTicket] = {}
    """Keeps track of the currently issued auth tickets by remote."""

    async def get(self):
        ws = web.WebSocketResponse()
        await ws.prepare(self.request)

        if self.request.remote not in self.current_challenges:
            await ws.close(code=1008, message="No current challenge, please generate one")
            return ws

        signed_message = await ws.receive_bytes(timeout=0.5)
        ticket = self.current_challenges[self.request.remote]

        # verify the signed challenge
        try:
            verify_key = VerifyKey(ticket.pub_key, encoder=RawEncoder)
            challenge = verify_key.verify(signed_message)
        except BadSignatureError as e:
            await ws.close(code=1008, message=e)
            return ws

        if not ticket.challenge == challenge:
            await ws.close(code=1008, message="Signed wrong message")
            return ws

        # handle messages
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
                else:
                    await ws.send_str(msg.data + '/answer')
            elif msg.type == WSMsgType.ERROR:
                print(f'ws connection closed with exception {ws.exception()}')

        return ws

    async def post(self):
        """
        Allows the bike to negotiate the private key and get a session key.
        The bike posts their public key, which is compared against all the bikes
        on the system. A challenge is generated and sent to the bike to
        verify their identity.
        """
        public_key = await self.request.read()
        if not any(bike["pub"] == public_key for bike in store.get_bikes()):
            raise web.HTTPUnauthorized(reason="Identity not recognized.")

        challenge = random(64)
        self.current_challenges[self.request.remote] = BikeTicket(public_key, challenge, datetime.now())
        return web.Response(body=challenge)


class BikeRentalsView(BaseView):
    """
    Gets the rentals for a single bike.
    """
    url = "/bikes/{id}/rentals"

    async def get(self):
        pass

    async def post(self):
        """
        Starts a new rental.

        If the rental could not be made, (not authenticated
        or bike in use) it will fail with the appropriate message.

        todo implement
        """
        pass

    async def patch(self):
        pass
