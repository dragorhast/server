"""
Pickup Point Related Views
---------------------------

Handles all the pick-up point CRUD

- Customer can reserve a bike from a rack
- Admin must be able to get bikes in use / available at each location
"""
from aiohttp import web
from aiohttp_apispec import docs

from server.models import PickupPoint, User
from server.permissions import requires, UserIsAdmin
from server.serializer import JSendSchema, JSendStatus
from server.serializer.decorators import returns, expects
from server.serializer.fields import Many
from server.serializer.models import PickupPointSchema, BikeSchema, ReservationSchema, CreateReservationSchema
from server.service.access.pickup_points import get_pickup_points, get_pickup_point
from server.service.access.reservations import get_reservations
from server.service.access.users import get_user
from server.service.manager.reservation_manager import ReservationError
from server.views.base import BaseView
from server.views.decorators import match_getter, GetFrom, Optional

PICKUP_IDENTIFIER_REGEX = "(?!shortages)[^{}/]+"


class PickupsView(BaseView):
    """
    Gets or adds to the list of all pick-up points.
    """
    url = "/pickups"
    name = "pickups"
    with_optional_user = match_getter(get_user, Optional("user"), firebase_id=Optional(GetFrom.AUTH_HEADER))

    @docs(summary="Get All Pickup Points")
    @with_optional_user
    @returns(JSendSchema.of(pickups=Many(PickupPointSchema())))
    async def get(self, user: User):
        pickups = {pickup: (None, None) for pickup in await get_pickup_points()}

        if user is not None and user.is_admin:
            pickups.update(self.reservation_sourcer.shortages())

        return {
            "status": JSendStatus.SUCCESS,
            "data": {"pickups": [
                pickup.serialize(self.reservation_manager, count, date)
                for pickup, (count, date) in pickups.items()
            ]}
        }

    @docs(summary="Create A Pickup Point")
    async def post(self):
        raise NotImplementedError()


class PickupView(BaseView):
    """
    Gets, updates or deletes a single pick-up point.
    """
    url = f"/pickups/{{id:{PICKUP_IDENTIFIER_REGEX}}}"
    name = "pickup"
    with_pickup = match_getter(get_pickup_point, 'pickup', pickup_id='id')
    with_user = match_getter(get_user, "user", firebase_id=GetFrom.AUTH_HEADER)

    @with_pickup
    @docs(summary="Get A Pickup Point")
    @returns(JSendSchema.of(pickup=PickupPointSchema()))
    async def get(self, pickup):
        pickup_data = pickup.serialize(self.reservation_manager)

        return {
            "status": JSendStatus.SUCCESS,
            "data": {"pickup": pickup_data}
        }

    @with_pickup
    @with_user
    @docs(summary="Delete A Pickup Point")
    @requires(UserIsAdmin())
    async def delete(self, pickup: PickupPoint, user: User):
        await pickup.delete()
        raise web.HTTPNoContent


class PickupBikesView(BaseView):
    """
    Gets list of bikes currently at a pickup point.
    """
    url = f"/pickups/{{id:{PICKUP_IDENTIFIER_REGEX}}}/bikes"
    with_pickup = match_getter(get_pickup_point, 'pickup', pickup_id='id')

    @with_pickup
    @docs(summary="Get All Bikes In Pickup Point")
    @returns(JSendSchema.of(bikes=Many(BikeSchema())))
    async def get(self, pickup: PickupPoint):
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"bikes": [
                bike.serialize(self.bike_connection_manager, self.rental_manager, self.reservation_manager) for bike in
                await self.reservation_manager.available_bikes(pickup)
            ]}
        }


class PickupReservationsView(BaseView):
    """
    Gets or adds to a pickup point's list of reservations.
    """
    url = f"/pickups/{{id:{PICKUP_IDENTIFIER_REGEX}}}/reservations"
    with_user = match_getter(get_user, "user", firebase_id=GetFrom.AUTH_HEADER)
    with_pickup = match_getter(get_pickup_point, "pickup", pickup_id="id")

    @with_user
    @docs(summary="Get All Reservations For Pickup Point")
    @requires(UserIsAdmin())
    @returns(JSendSchema.of(reservations=Many(ReservationSchema())))
    async def get(self, user):
        reservation_ids = self.reservation_manager.reservations_in(self.request.match_info["id"])
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"reservations": [
                reservation.serialize(self.request.app.router, self.reservation_manager)
                for reservation in await get_reservations(*reservation_ids)
            ]}
        }

    @with_pickup
    @with_user
    @docs(summary="Create Reservation At Pickup Point")
    @expects(CreateReservationSchema())
    @returns(
        error=JSendSchema(),
        success=JSendSchema.of(reservation=ReservationSchema())
    )
    async def post(self, user, pickup):
        """
        To claim a reservation, simply rent a bike from the same pickup point as you usually
        would do. This will automatically claim that bike for you, ending your reservation,
        and starting your rental.
        """
        time = self.request["data"]["reserved_for"]
        try:
            reservation = await self.reservation_manager.reserve(user, pickup, time)
        except ReservationError as e:
            return "error", {
                "status": JSendStatus.FAIL,
                "data": {"message": str(e)}
            }
        else:
            return "success", {
                "status": JSendStatus.SUCCESS,
                "data": {"reservation": reservation.serialize(self.request.app.router, self.reservation_manager)}
            }


class PickupShortagesView(BaseView):
    """
    Gets all pickup points with shortages.
    """

    url = "/pickups/shortages"
    with_user = match_getter(get_user, "user", firebase_id=GetFrom.AUTH_HEADER)

    @with_user
    @requires(UserIsAdmin())
    @returns(JSendSchema.of(pickups=Many(PickupPointSchema())))
    async def get(self, user: User):
        shortages = self.reservation_sourcer.shortages()
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"pickups": [pickup.serialize(self.reservation_manager, count, date) for pickup, (count, date) in
                                 shortages.items()]}
        }
