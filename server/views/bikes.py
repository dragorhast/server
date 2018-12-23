"""
Handles all the bike CRUD
"""

from aiohttp import web, WSMsgType
from marshmallow import Schema, ValidationError
from marshmallow.fields import String
from nacl.encoding import RawEncoder
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from server import logger
from server.models.bike import BikeType, Bike
from server.serializer import BikeSchema, RentalSchema
from server.serializer.fields import BytesField, EnumField
from server.serializer.jsend import JSendStatus, JSendSchema
from server.service import get_bike, get_bikes, register_bike, get_rentals, get_user, \
    lock_bike, BadKeyException
from server.ticket_store import TicketStore
from server.views.base import BaseView
from server.views.utils import getter


class BikesView(BaseView):
    """
    Gets the bikes, or adds a new bike.

    .. versionadded:: 0.1.0
    """
    url = "/bikes"

    async def get(self):
        """Gets all the bikes from the system."""
        response_schema = JSendSchema.of(BikeSchema(), many=True)

        response = response_schema.dump({
            "status": JSendStatus.SUCCESS,
            "data": (bike.serialize() for bike in await get_bikes())
        })

        return web.json_response(response)

    async def post(self):
        """
        Registers a bike with the system.
        """
        bike_data = await self.request.json()
        request_schema = BikeRegisterSchema()
        response_schema = JSendSchema()

        try:
            bike_data = request_schema.load(bike_data)
        except ValidationError as e:
            response = response_schema.dump({
                "status": JSendStatus.FAIL,
                "data": e.args[0]
            })
            return web.json_response(response, status=400)

        try:
            bike = await register_bike(bike_data["public_key"], bike_data["master_key"])
        except (ValueError, BadKeyException) as e:
            response = response_schema.dump({
                "status": JSendStatus.FAIL,
                "data": e.args if isinstance(e, ValueError) else "Incorrect master key"
            })
            return web.json_response(response, status=400)

        response = response_schema.dump({
            "status": JSendStatus.SUCCESS,
            "data": bike.serialize()
        })
        return web.json_response(response)


class BikeView(BaseView):
    """
    Gets or updates a single bike.
    """
    url = "/bikes/{id:[0-9]+}"
    bike_getter = getter(get_bike, 'id', 'bike_id')

    @bike_getter
    async def get(self, bike):
        """Gets a single bike by its id."""
        response_schema = JSendSchema.of(BikeSchema())

        response = response_schema.dump({
            "status": JSendStatus.SUCCESS,
            "data": bike.serialize()
        })

        return web.json_response(response)

    @bike_getter
    async def delete(self, bike):
        """Deletes a bike by its id."""
        pass

    @bike_getter
    async def patch(self, bike):
        data = await self.request.json()

        if "locked" not in data:
            raise web.HTTPBadRequest(reason="Must specify locked or not.")

        try:
            await lock_bike("", True)
        except Exception:
            raise web.HTTPServiceUnavailable(reason="Requested bike not connected to server.")

        return web.Response(text="updated")

    @bike_getter
    async def put(self, bike):
        pass


class BikeRentalsView(BaseView):
    """
    Gets the rentals for a single bike.
    """
    url = "/bikes/{id:[0-9]+}/rentals"
    bike_getter = getter(get_bike, 'id', 'bike_id')

    @bike_getter
    async def get(self, bike: Bike):
        response_schema = JSendSchema.of(RentalSchema(), many=True)

        response = response_schema.dump({
            "status": JSendStatus.SUCCESS,
            "data": (rental.serialize() for rental in await get_rentals(bike=bike))
        })

        return web.json_response(response)

    @bike_getter
    async def post(self, bike):
        """
        Starts a new rental.

        If the rental could not be made, (not authenticated
        or bike in use) it will fail with the appropriate message.
        """
        user = await get_user()
        rental = await start_rental(bike, user)
        return web.json_response(rental.serialize())


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
        socket = web.WebSocketResponse()
        await socket.prepare(self.request)
        remote = self.request.remote

        public_key = await socket.receive_bytes(timeout=0.5)
        signature = await socket.receive_bytes(timeout=0.5)

        try:
            ticket = self.open_tickets.pop_ticket(remote, public_key)
        except KeyError:
            await socket.send_str("fail:no_ticket")
            return socket

        # verify the signed challenge
        try:
            verify_key = VerifyKey(ticket.bike.public_key, encoder=RawEncoder)
            verify_key.verify(ticket.challenge, signature)
        except BadSignatureError:
            await socket.send_str("fail:invalid_sig")
            return socket
        else:
            await socket.send_str("verified")
            status = await socket.receive_json()
            if "locked" in status:
                ticket.bike.locked = status["locked"]

        try:
            # handle messages
            logger.info("Bike %s connected", ticket.bike.id)
            self.request.app['bike_connections'].add(socket)
            ticket.bike.socket = socket

            async for msg in socket:
                if msg.type == WSMsgType.TEXT:
                    if msg.data == 'close':
                        await socket.close()
                    else:
                        await socket.send_str(msg.data + '/answer')
                elif msg.type == WSMsgType.ERROR:
                    print('ws connection closed with exception %s', socket.exception())
        finally:
            logger.info("Bike %s disconnected", ticket.bike.id)
            self.request.app['bike_connections'].discard(socket)

        return socket

    async def post(self):
        """
        Allows the bike to negotiate the private key and get a session key.
        The bike posts their public key, which is compared against all the bikes
        on the system. A challenge is generated and sent to the bike to
        verify their identity.
        """
        public_key = await self.request.read()
        bike = [bike for bike in await get_bikes() if bike.public_key == public_key]
        if not bike:
            raise web.HTTPUnauthorized(reason="Identity not recognized.")
        bike = bike[0]

        challenge = self.open_tickets.add_ticket(self.request.remote, bike)
        return web.Response(body=challenge)


class BikeRegisterSchema(Schema):
    """The schema of the bike register request."""

    public_key = BytesField(required=True)
    """The public key of the bike."""

    master_key = BytesField()
    """The master key, used to register the bike."""

    type = EnumField(BikeType)
    """The type of bike."""
