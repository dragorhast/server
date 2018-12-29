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
from server.models.bike import Bike
from server.models.util import BikeType
from server.permissions import AuthenticatedPermission
from server.permissions.util import require_user_permission
from server.serializer import BikeSchema, RentalSchema, BytesField, EnumField, JSendStatus, JSendSchema
from server.service import TicketStore, rental_manager
from server.service.bikes import get_bikes, get_bike, register_bike, lock_bike, BadKeyError, delete_bike
from server.service.rentals import get_rentals_for_bike
from server.service.users import get_user
from server.token_verify import TokenVerificationError
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
                "data": e.messages
            })
            return web.json_response(response, status=400)

        try:
            bike = await register_bike(bike_data["public_key"], bike_data["master_key"])
        except (ValueError, BadKeyError) as e:
            response = response_schema.dump({
                "status": JSendStatus.FAIL,
                "data": e.args
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
        request_schema = MasterKeySchema()
        response_schema = JSendSchema()

        try:
            request_data = request_schema.load(await self.request.json())
        except ValidationError as e:
            response = response_schema.dump({
                "status": JSendStatus.FAIL,
                "data": e.messages
            })
            return web.json_response(response, status=400)

        try:
            await delete_bike(bike, request_data["master_key"])
        except BadKeyError as e:
            response = response_schema.dump({
                "status": JSendStatus.FAIL,
                "data": e.args
            })
            return web.json_response(response, status=400)

        raise web.HTTPNoContent

    @bike_getter
    async def patch(self, bike):
        data = await self.request.json()

        if "locked" not in data:
            raise web.HTTPBadRequest(reason="Must specify locked or not.")

        try:
            await lock_bike("", True)
        except ConnectionError as exp:
            raise web.HTTPServiceUnavailable(reason="Requested bike not connected to server.") from exp

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
            "data": (rental.serialize() for rental in await get_rentals_for_bike(bike=bike))
        })

        return web.json_response(response)

    @bike_getter
    @require_user_permission(AuthenticatedPermission())
    async def post(self, bike):
        """
        Starts a new rental.

        If the rental could not be made, (not authenticated
        or bike in use) it will fail with the appropriate message.
        """
        response_schema = JSendSchema.of(RentalSchema())

        try:
            user = await get_user(firebase_id=request["firebase_id"])
        except TokenVerificationError:
            response_schema = JSendSchema()
            response_data = response_schema.dump({
                "status": JSendStatus.FAIL,
                "data": {"firebase_id": f"Firebase token is invalid. Log back in to firebase and try again."}
            })
            return web.json_response(response_data)

        if user is None:
            response_schema = JSendSchema()
            response_data = response_schema.dump({
                "status": JSendStatus.FAIL,
                "data": {"firebase_id": f"No such user exists, but your key is valid."
                f"Create a new one at '{self.request.app.router['users'].url_for()}'."}
            })
            return web.json_response(response_data)

        rental = await rental_manager.create(user, bike)

        response_data = response_schema.dump(rental.serialize())
        return web.json_response(response_data)


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

    For more detail about the auth process, see :doc:`/bike-protocol`.
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


class AuthorizedSchema(Schema):
    """The schema to start a bike rental."""

    firebase_id = String()
    """The user to start the rental as."""


class MasterKeySchema(Schema):
    master_key = BytesField(required=True)
    """The master key, used to perform operations on the bike."""


class BikeRegisterSchema(MasterKeySchema):
    """The schema of the bike register request."""

    public_key = BytesField(required=True)
    """The public key of the bike."""

    type = EnumField(BikeType)
    """The type of bike."""
