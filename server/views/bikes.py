"""
Bike Related Views
-------------------------

Handles all the bike CRUD
"""
from functools import partial
from json import JSONDecodeError
from typing import List

from aiohttp import web, WSMessage
from aiohttp_apispec import docs
from marshmallow.fields import Float
from nacl.encoding import RawEncoder
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from shapely.geometry import Point

from server import logger
from server.models import Issue, User
from server.models.bike import Bike
from server.models.user import UserType
from server.permissions import requires, UserIsAdmin, UserIsRentingBike, BikeIsConnected, BikeNotInUse, BikeNotBroken, \
    UserMatchesToken
from server.permissions.users import UserCanPay
from server.serializer import JSendStatus, JSendSchema
from server.serializer.decorators import returns, expects
from server.serializer.fields import Many
from server.serializer.json_rpc import JsonRPCRequest, JsonRPCResponse
from server.serializer.misc import MasterKeySchema, BikeRegisterSchema, BikeModifySchema
from server.serializer.models import CurrentRentalSchema, IssueSchema, BikeSchema, RentalSchema
from server.service import TicketStore, ActiveRentalError
from server.service.access.bikes import get_bikes, get_bike, register_bike, BadKeyError, delete_bike, \
    set_bike_in_circulation
from server.service.access.issues import get_issues, get_broken_bikes, open_issue
from server.service.access.rentals import get_rentals_for_bike
from server.service.access.reservations import current_reservations
from server.service.access.users import get_user
from server.service.manager.reservation_manager import ReservationError, CollectionError
from server.views.base import BaseView
from server.views.decorators import match_getter, GetFrom, Optional

BIKE_IDENTIFIER_REGEX = "(?!connect|broken|low|closest)[^{}/]+"


class BikesView(BaseView):
    """
    Gets the bikes, or adds a new bike.
    """
    url = "/bikes"
    with_user = match_getter(get_user, Optional("user"), firebase_id=Optional(GetFrom.AUTH_HEADER))

    @with_user
    @docs(summary="Get All Bikes")
    @returns(JSendSchema.of(
        bikes=Many(BikeSchema(exclude=("public_key",)))))
    async def get(self, user):
        """Gets all the bikes from the system."""
        bikes = [bike.serialize(
            self.bike_connection_manager,
            self.rental_manager,
            self.reservation_manager,
            include_location=user is not None and user.type is not UserType.USER
        ) for bike in await get_bikes()]

        if self.request.query.get("available") == "true":
            bikes = (bike for bike in bikes if bike["status"] == "available")

        return {
            "status": JSendStatus.SUCCESS,
            "data": {"bikes": bikes}
        }

    @docs(summary="Register New Bike")
    @expects(BikeRegisterSchema())
    @returns(
        bad_key=(JSendSchema(), web.HTTPBadRequest),
        registered=JSendSchema.of(bike=BikeSchema(only=('identifier', 'available')))
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
                "data": {"bike": bike.serialize(
                    self.bike_connection_manager, self.rental_manager, self.reservation_manager
                )}
            }


class BrokenBikesView(BaseView):
    """
    Gets the list of bikes with active issues, along with the open issues for those bikes.
    """
    url = "/bikes/broken"
    with_bikes = match_getter(get_broken_bikes, "broken_bikes")
    with_admin = match_getter(get_user, "user", firebase_id=GetFrom.AUTH_HEADER)

    @with_admin
    @with_bikes
    @docs(summary="Get All Broken Bikes")
    @requires(UserIsAdmin())
    @returns(JSendSchema.of(bikes=Many(BikeSchema())))
    async def get(self, user, broken_bikes):
        """
        A broken bike is one that has at least one issue open. Broken bikes must be
        serviced, and so their status is shown here for use by the operators. These
        bikes can be loaded into a path-finding algorithm and serviced as needed.
        """
        return {
            "status": JSendStatus.SUCCESS,
            "data": {
                "bikes": [
                    bike.serialize(self.bike_connection_manager, self.rental_manager, self.reservation_manager,
                                   issues=issues)
                    for bike, issues in broken_bikes
                ]
            }
        }


class LowBikesView(BaseView):
    url = "/bikes/low"

    @docs(summary="Get All Low Battery Bikes")
    @returns(JSendSchema.of(bikes=Many(BikeSchema(only=("identifier", "battery", "current_location")))))
    async def get(self):
        """
        There may come a point where a bike hasn't been able to generate enough power
        to sustain its battery level. The that point (30% battery or lower), the bike
        will be listed here. If you claim and recharge one of these bikes, you will
        receive discounts on your next trip proportional to the amount charged. These
        stack up.

        If, for example, you charged 5 bikes for 92, 45, 37, 78, and 83 percent each
        then your next 5 rides will be 92% off, then 45% off, etc.
        """
        low_battery_bikes = await self.bike_connection_manager.low_battery(30)
        serialized_bikes = [
            bike.serialize(self.bike_connection_manager, self.rental_manager, self.reservation_manager)
            for bike in low_battery_bikes
        ]

        serialized_bikes = [bike for bike in serialized_bikes if bike["available"]]

        return {
            "status": JSendStatus.SUCCESS,
            "data": {"bikes": serialized_bikes}
        }


class BikeView(BaseView):
    """
    Gets or updates a single bike.
    """
    url = f"/bikes/{{identifier:{BIKE_IDENTIFIER_REGEX}}}"
    name = "bike"
    with_bike = match_getter(get_bike, 'bike', identifier=('identifier', str))
    with_user = match_getter(get_user, Optional('user'), firebase_id=Optional(GetFrom.AUTH_HEADER))
    with_rental = match_getter(get_rentals_for_bike)

    @with_bike
    @with_user
    @docs(summary="Get A Bike")
    @returns(JSendSchema.of(bike=BikeSchema(exclude=("public_key",))))
    async def get(self, bike: Bike, user):
        """Gets a single bike by its id."""
        return {
            "status": JSendStatus.SUCCESS,
            "data": {
                "bike": bike.serialize(
                    self.bike_connection_manager, self.rental_manager, self.reservation_manager,
                    include_location=user is not None and self.rental_manager.is_renting(user.id, bike.id)
                )}
        }

    @with_bike
    @docs(summary="Delete A Bike")
    @expects(MasterKeySchema())
    @returns(
        bad_master=(JSendSchema(), web.HTTPBadRequest)
    )
    async def delete(self, bike: Bike):
        """Deletes a bike by its id."""
        try:
            await delete_bike(bike, self.request["data"]["master_key"])
        except BadKeyError as error:
            return "bad_master", {
                "status": JSendStatus.FAIL,
                "data": {
                    "message": "The supplied master key is invalid.",
                    "errors": error.args
                }
            }
        else:
            raise web.HTTPNoContent

    @with_user
    @with_bike
    @docs(summary="Update A Bike")
    @requires(UserIsAdmin() | UserIsRentingBike() & BikeIsConnected())
    @expects(BikeModifySchema())
    @returns(JSendSchema.of(bike=BikeSchema(exclude=("public_key",))))
    async def patch(self, user: User, bike: Bike):
        """
        Allows users to update the status of a bike.

        - locked status
        - circulation status
        """
        if "locked" in self.request["data"]:
            await self.bike_connection_manager.set_locked(bike.id, self.request["data"]["locked"])

        if user.type is not UserType.USER and "in_circulation" in self.request["data"]:
            bike = await set_bike_in_circulation(bike, self.request["data"]["in_circulation"])

        return {
            "status": JSendStatus.SUCCESS,
            "data": {
                "bike": bike.serialize(self.bike_connection_manager, self.rental_manager, self.reservation_manager,
                                       include_location=True)}
        }


class ClosestBikeView(BaseView):
    """
    Gets or updates a single bike.
    """
    url = f"/bikes/closest"
    name = "closest_bike"

    @docs(summary="Get The Closest Bike")
    @returns(JSendSchema.of(bike=BikeSchema(exclude=("public_key",)), distance=Float()))
    async def get(self):
        """Gets a single bike by its id."""
        lat = self.request.query["lat"]
        long = self.request.query["lng"]
        user_location = Point(float(long), float(lat))
        bike, distance = await self.bike_connection_manager.closest_available_bike(user_location, self.rental_manager,
                                                                                   self.reservation_manager)

        if bike is None:
            raise web.HTTPNotFound
        else:
            return {
                "status": JSendStatus.SUCCESS,
                "data": {
                    "bike": bike.serialize(self.bike_connection_manager, self.rental_manager,
                                           self.reservation_manager),
                    "distance": distance
                }
            }


class BikeRentalsView(BaseView):
    """
    Gets the rentals for a single bike.
    """
    url = f"/bikes/{{identifier:{BIKE_IDENTIFIER_REGEX}}}/rentals"
    with_bike = match_getter(get_bike, 'bike', identifier=('identifier', str))
    with_user = match_getter(get_user, 'user', firebase_id=GetFrom.AUTH_HEADER)

    @with_bike
    @with_user
    @docs(summary="Get Past Rentals For Bike")
    @requires(UserIsAdmin())
    @returns(JSendSchema.of(rentals=Many(RentalSchema())))
    async def get(self, bike: Bike, user):
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"rentals": [
                await rental.serialize(self.rental_manager, self.bike_connection_manager, self.reservation_manager,
                                       self.request.app.router)
                for rental in await get_rentals_for_bike(bike=bike)
            ]}
        }

    @with_bike
    @with_user
    @docs(summary="Start A New Rental")
    @requires(UserMatchesToken() & UserCanPay() & BikeNotInUse() & BikeNotBroken(max_issues=1))
    @returns(
        rental_created=JSendSchema.of(rental=CurrentRentalSchema(exclude=('user', 'bike', 'events'))),
        active_rental=JSendSchema(),
        reservation_error=JSendSchema()
    )
    async def post(self, bike: Bike, user: User):
        """
        It is most logical that a rental is created on a bike resource.
        This metaphor matches real life the best, as it resembles picking bike off the rack.
        A user may start a rental on any bike that is not currently in use, by simply
        sending a POST request to the bike's rentals resource ``/api/v1/bikes/rentals``
        with the user's firebase token.
        """
        reservations = await current_reservations(user)

        if reservations:
            try:
                rental, start_location = await self.reservation_manager.claim(user, bike)
            except CollectionError:
                # they can try and rent it normally
                reservations = []
            except ReservationError as e:
                return "reservation_error", {
                    "status": JSendStatus.FAIL,
                    "data": {
                        "message": str(e)
                    }
                }
            except ActiveRentalError as e:
                return "active_rental", {
                    "status": JSendStatus.FAIL,
                    "data": {
                        "message": "You already have an active rental!",
                        "rental_id": e.rental_id,
                        "url": str(self.request.app.router["me"].url_for(tail="/rentals/current"))
                    }
                }

        if not reservations:
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

        return "rental_created", {
            "status": JSendStatus.SUCCESS,
            "data": {"rental": await rental.serialize(
                self.rental_manager, self.bike_connection_manager, self.reservation_manager, self.request.app.router,
                start_location=start_location,
                current_location=start_location
            )}
        }


class BikeIssuesView(BaseView):
    url = f"/bikes/{{identifier:{BIKE_IDENTIFIER_REGEX}}}/issues"
    with_issues = match_getter(partial(get_issues, is_active=True), 'issues', bike=('identifier', str))
    with_bike = match_getter(get_bike, 'bike', identifier=('identifier', str))
    with_user = match_getter(get_user, "user", firebase_id=GetFrom.AUTH_HEADER)

    @with_issues
    @with_user
    @docs(summary="Get All Open Issues On Bike")
    @requires(UserIsAdmin())
    @returns(JSendSchema.of(issues=Many(IssueSchema())))
    async def get(self, issues: List[Issue], user):
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"issues": [issue.serialize(self.request.app.router) for issue in issues]}
        }

    @with_user
    @with_bike
    @docs(summary="Open A New Issue About Bike")
    @expects(IssueSchema(only=('description',)))
    @returns(JSendSchema.of(
        issue=IssueSchema(only=('id', 'user_id', 'user_url', 'bike_identifier', 'description', 'opened_at')))
    )
    async def post(self, user, bike):
        issue = await open_issue(
            description=self.request["data"]["description"],
            user=user,
            bike=bike
        )

        return {
            "status": JSendStatus.SUCCESS,
            "data": {"issue": issue.serialize(self.request.app.router)}
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

    @docs(summary="Connect Bike Socket")
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

        logger.info("Bike %s connected", ticket.bike.id)
        await self.bike_connection_manager.add_connection(ticket.bike, socket)
        ticket.bike.socket = socket

        await socket.send_str("verified")
        status = await socket.receive_json()
        if "locked" in status:
            self.bike_connection_manager.update_locked(ticket.bike.id, status["locked"])

        try:
            async for msg in socket:
                msg: WSMessage = msg
                try:
                    data = msg.json()
                except JSONDecodeError:
                    continue
                else:
                    if "method" in data:
                        valid_data = JsonRPCRequest().load(data)
                        if "id" not in valid_data and valid_data["method"] == "location_update":
                            point = Point(valid_data["params"]["long"], valid_data["params"]["lat"])
                            await self.bike_connection_manager.update_location(ticket.bike.id, point)
                            self.bike_connection_manager.update_battery(ticket.bike.id, valid_data["params"]["bat"])
                    else:
                        valid_data = JsonRPCResponse().load(data)
                        await self.bike_connection_manager.resolve_command(
                            ticket.bike.id, valid_data["id"], valid_data["result"])
        finally:
            logger.info("Bike %s disconnected", ticket.bike.id)
            await socket.close()
            del self.bike_connection_manager._bike_connections[ticket.bike.id]
            del ticket
            del socket

    @docs(summary="Create Bike Ticket")
    async def post(self):
        """
        Allows the bike to negotiate the private key and get a session key.
        The bike posts their public key, which is compared against all the bikes
        on the system. A challenge is generated and sent to the bike to
        verify their identity.
        """
        public_key = await self.request.read()
        bike = await get_bike(public_key=public_key)
        if bike is None:
            raise web.HTTPUnauthorized(reason="Identity not recognized.")

        challenge = self.open_tickets.add_ticket(self.request.remote, bike)
        return web.Response(body=challenge)
