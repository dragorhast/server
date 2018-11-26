"""
Handles all the bike CRUD
"""

from aiohttp import web, WSMsgType
from nacl.encoding import RawEncoder
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from nacl.utils import random

from server import logger, Store
from server.store.ticket_store import BikeConnectionTicket, TicketStore
from server.views.base import BaseView
from server.views.utils import getter


class BikesView(BaseView):
    """
    Gets the bikes, or adds a new bike.
    """
    url = "/bikes"

    async def get(self):
        return web.json_response(list(bike.serialize() for bike in Store.get_bikes()))

    async def post(self):
        pass


class BikeView(BaseView):
    """
    Gets or updates a single bike.
    """
    url = "/bikes/{id:[0-9]+}"
    bike_getter = getter(Store.get_bike, 'id', 'bike_id')

    @bike_getter
    async def get(self, bike):
        return web.json_response(bike.serialize())

    @bike_getter
    async def delete(self, bike):
        pass

    @bike_getter
    async def patch(self, bike):
        data = await self.request.json()

        if "locked" in data:
            await bike.set_locked(data["locked"])

        return web.Response(text="updated")

    @bike_getter
    async def put(self, bike):
        pass


class BikeRentalsView(BaseView):
    """
    Gets the rentals for a single bike.
    """
    url = "/bikes/{id:[0-9]+}/rentals"
    bike_getter = getter(Store.get_bike, 'id', 'bike_id')

    @bike_getter
    async def get(self, bike):
        pass

    @bike_getter
    async def post(self, bike):
        """
        Starts a new rental.

        If the rental could not be made, (not authenticated
        or bike in use) it will fail with the appropriate message.

        todo implement
        """
        pass

    @bike_getter
    async def patch(self, bike):
        pass


class BikeSocketView(BaseView):
    """
    Provides an endpoint for the server to communicate with the bikes.

    The bike posts to the url with their public key, which generates a ticket.
    The challenge is returned to the bike. The bike signs the challenge to prove
    their identity when setting up the connection. If the signed key is valid,
    the connection is accepted.

    When the websocket is opened, the client sends their public key to the
    server followed by the challenge. They should expect to receive a "verified"
    response in return.

    .. code-block:: python

        challenge, ticket_id = create_ticket(public_key)
        signed_challenge = signing_key.sign(challenge)
        await ws.send_bytes(public_key)
        await ws.send_bytes(signed_challenge)
        if not await ws.receive_str() == "verified":
            raise Exception

    For more detail about the auth process, see :doc:`/communication`.
    """

    url = "/bikes/connect"

    open_tickets = TicketStore()
    """Maps a public key to their currently issued ticket."""

    async def get(self):
        """
        Initiates the websocket connection between the
        bike and the server. Requires an open ticket
        (which can be created by posting) to succeed.
        """
        ws = web.WebSocketResponse()
        await ws.prepare(self.request)
        remote = self.request.remote

        if remote not in self.open_tickets:
            await ws.close(code=1008, message="No current challenge, please generate one")
            return ws

        signed_message = await ws.receive_bytes(timeout=0.5)
        ticket = self.open_tickets.take_ticket(remote)

        # verify the signed challenge
        try:
            verify_key = VerifyKey(ticket.pub_key, encoder=RawEncoder)
            challenge = verify_key.verify(signed_message)
        except BadSignatureError as e:
            await ws.send_str("rip")
            await ws.close(code=1008, message=e)
            return ws

        if not ticket.challenge == challenge:
            await ws.send_str("rip")
            await ws.close(code=1008, message="Signed wrong message")
            return ws
        else:
            await ws.send_str("verified")

        del self.open_tickets[remote]

        try:
            # handle messages
            logger.info(f"Bike {ticket.bike.bid} connected")
            self.request.app['bike_connections'].add(ws)
            ticket.bike.socket = ws

            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    if msg.data == 'close':
                        await ws.close()
                    else:
                        await ws.send_str(msg.data + '/answer')
                elif msg.type == WSMsgType.ERROR:
                    print(f'ws connection closed with exception {ws.exception()}')
        finally:
            logger.info(f"Bike {ticket.bike.bid} disconnected")
            self.request.app['bike_connections'].discard(ws)

        return ws

    async def post(self):
        """
        Allows the bike to negotiate the private key and get a session key.
        The bike posts their public key, which is compared against all the bikes
        on the system. A challenge is generated and sent to the bike to
        verify their identity.
        """
        public_key = await self.request.read()
        if not any(bike.pub == public_key for bike in Store.get_bikes()):
            raise web.HTTPUnauthorized(reason="Identity not recognized.")

        challenge = random(64)
        self.open_tickets.add_ticket(
            self.request.remote,
            BikeConnectionTicket(public_key, challenge, Store.get_bike(public_key=public_key))
        )
        return web.Response(body=challenge)
