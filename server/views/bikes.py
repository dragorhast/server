"""
Bike Related Views
-------------------------

Handles all the bike CRUD
"""
from http import HTTPStatus
from typing import List

from aiohttp import web, WSMsgType
from marshmallow import Schema
from nacl.encoding import RawEncoder
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from server import logger
from server.models import Issue
from server.models.bike import Bike
from server.models.util import BikeType
from server.permissions.decorators import requires
from server.permissions.permissions import BikeNotInUse, UserIsAdmin
from server.serializer import BikeSchema, RentalSchema, BytesField, EnumField, JSendStatus, JSendSchema
from server.serializer.decorators import returns, expects
from server.serializer.fields import Many
from server.serializer.models import CurrentRentalSchema, IssueSchema
from server.service import TicketStore, ActiveRentalError
from server.service.bikes import get_bikes, get_bike, register_bike, BadKeyError, delete_bike
from server.service.issues import get_issues
from server.service.rentals import get_rentals_for_bike
from server.service.users import get_user
from server.views.base import BaseView
from server.views.utils import match_getter, GetFrom


class MasterKeySchema(Schema):
    master_key = BytesField(required=True)
    """The master key, used to perform operations on the bike."""


class BikeRegisterSchema(MasterKeySchema):
    """The schema of the bike register request."""

    public_key = BytesField(required=True)
    """The public key of the bike."""

    type = EnumField(BikeType)
    """The type of bike."""


class BikesView(BaseView):
    """
    Gets the bikes, or adds a new bike.

    .. versionadded:: 0.1.0
    """
    url = "/bikes"

    @returns(JSendSchema.of(bikes=Many(BikeSchema(only=("public_key", "current_location")))))
    async def get(self):
        """Gets all the bikes from the system."""
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"bikes": [bike.serialize(self.bike_connection_manager) for bike in await get_bikes()]}
        }

    @expects(BikeRegisterSchema())
    @returns(
        bad_key=(JSendSchema(), HTTPStatus.BAD_REQUEST),
        registered=JSendSchema.of(bike=BikeSchema(only=('public_key',)))
    )
    async def post(self):
        """ Registers a bike with the system."""
        try:
            bike = await register_bike(
                self.request["data"]["public_key"],
                self.request["data"]["master_key"]
            )
        except BadKeyError as error:
            return "bad_key", {
                "status": JSendStatus.FAIL,
                "data": {
                    "message": "The supplied master key is invalid.",
                    "errors": error.args
                },
            }
        else:
            return "registered", {
                "status": JSendStatus.SUCCESS,
                "data": bike.serialize(self.bike_connection_manager)
            }


class BikeView(BaseView):
    """
    Gets or updates a single bike.
    """
    url = "/bikes/{identifier}"
    name = "bike"
    with_bike = match_getter(get_bike, 'bike', identifier=('identifier', str))

    @with_bike
    @returns(JSendSchema.of(bike=BikeSchema(only=("public_key",))))
    async def get(self, bike: Bike):
        """Gets a single bike by its id."""
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"bike": bike.serialize(self.bike_connection_manager)}
        }

    @with_bike
    @expects(MasterKeySchema())
    @returns(JSendSchema(), HTTPStatus.BAD_REQUEST)
    async def delete(self, bike: Bike):
        """Deletes a bike by its id."""
        try:
            await delete_bike(bike, self.request["data"]["master_key"])
        except BadKeyError as error:
            return {
                "status": JSendStatus.FAIL,
                "data": {
                    "message": "The supplied master key is invalid.",
                    "errors": error.args
                }
            }
        else:
            raise web.HTTPNoContent

    @with_bike
    async def patch(self, bike):
        raise NotImplementedError()

    @with_bike
    async def put(self, bike):
        raise NotImplementedError()


class BikeRentalsView(BaseView):
    """
    Gets the rentals for a single bike.
    """
    url = "/bikes/{identifier}/rentals"
    with_bike = match_getter(get_bike, 'bike', identifier=('identifier', str))
    with_user = match_getter(get_user, 'user', firebase_id=GetFrom.AUTH_HEADER)

    @with_bike
    @with_user
    @requires(UserIsAdmin())
    @returns(JSendSchema.of(rentals=Many(RentalSchema())))
    async def get(self, bike: Bike, user):
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"rentals": [await rental.serialize(self.rental_manager, self.request.app.router) for rental in
                                 (await get_rentals_for_bike(bike=bike))]}
        }

    @with_bike
    @with_user
    @requires(BikeNotInUse())
    @returns(
        missing_user=JSendSchema(),
        rental_created=JSendSchema.of(rental=CurrentRentalSchema(only=(
            'id', 'user_id', 'user_url', 'bike_identifier', 'bike_url', 'start_location',
            'current_location', 'start_time', 'estimated_price', 'is_active'
        ))),
        active_rental=JSendSchema()
    )
    async def post(self, bike: Bike, user):
        """
        Starts a new rental.

        If the rental could not be made, (not authenticated
        or bike in use) it will fail with the appropriate message.
        """
        user = await get_user(firebase_id=self.request["token"])

        if user is None:
            return "missing_user", {
                "status": JSendStatus.FAIL,
                "data": {
                    "message":
                        f"No such user exists, but your key is valid. "
                        f"Create a new one at '{self.request.app.router['users'].url_for()}'."
                }
            }
        else:
            try:
                rental, start_location = await self.rental_manager.create(user, bike)
            except ActiveRentalError as e:
                return "active_rental", {
                    "status": JSendStatus.FAIL,
                    "data": {
                        "message": "You already have an active rental!",
                        "rental_id": e.rental_id,
                        "url": str(self.request.app.router["me"].url_for(tail="/rentals/current"))
                    }
                }
            else:
                return "rental_created", {
                    "status": JSendStatus.SUCCESS,
                    "data": {"rental": await rental.serialize(
                        self.rental_manager, self.request.app.router,
                        start_location=start_location,
                        current_location=start_location
                    )}
                }


class BikeIssuesView(BaseView):
    url = "/bikes/{identifier}/issues"
    with_issues = match_getter(get_issues, 'issues', bike=('identifier', str))

    @with_issues
    @returns(JSendSchema.of(issues=Many(IssueSchema())))
    async def get(self, issues: List[Issue]):
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"issues": [issue.serialize(self.request.app.router) for issue in issues]}
        }


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

    For more detail about the auth process, see :doc:`/design/bike-protocol`.
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
            await self.bike_connection_manager.add_connection(ticket.bike, socket)
            ticket.bike.socket = socket

            async for msg in socket:
                if msg.type == WSMsgType.TEXT:
                    logger.info(msg)
                elif msg.type == WSMsgType.ERROR:
                    print('ws connection closed with exception %s', socket.exception())
        finally:
            logger.info("Bike %s disconnected", ticket.bike.id)

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
