"""
Reservation Related Views
--------------------------------

Handles all the reservations CRUD

To create a new reservation, go through the pickup point.
"""
from aiohttp_apispec import docs

from server.permissions import UserIsAdmin, requires
from server.permissions.users import UserOwnsReservation
from server.serializer import JSendStatus, returns, JSendSchema
from server.serializer.fields import Many
from server.serializer.models import ReservationSchema
from server.service.access.reservations import get_reservation, get_reservations
from server.service.access.users import get_user
from server.views.base import BaseView
from server.views.decorators import match_getter, GetFrom


class ReservationsView(BaseView):
    """
    Gets the list of reservations.
    """
    url = "/reservations"

    with_user = match_getter(get_user, 'user', firebase_id=GetFrom.AUTH_HEADER)

    @with_user
    @docs(summary="Get All Reservations")
    @requires(UserIsAdmin())
    @returns(JSendSchema.of(reservations=Many(ReservationSchema())))
    async def get(self, user):
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"reservations": [
                reservation.serialize(self.request.app.router) for reservation in await get_reservations()
            ]}
        }


class ReservationView(BaseView):
    """
    Gets or updates a single reservation.
    """
    url = "/reservations/{id}"
    with_reservation = match_getter(get_reservation, 'reservation', rid="id")
    with_user = match_getter(get_user, 'user', firebase_id=GetFrom.AUTH_HEADER)

    @with_user
    @with_reservation
    @docs(summary="Get A Reservation")
    @requires(UserIsAdmin() | UserOwnsReservation())
    @returns(JSendSchema.of(reservation=ReservationSchema()))
    async def get(self, reservation, user):
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"reservation": reservation.serialize(self.request.app.router)}
        }
