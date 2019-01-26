"""
Rental Related Views
---------------------------

Handles all the rentals CRUD.

To start a rental, go through the bike.
"""

from server.models import Rental
from server.permissions.decorators import requires
from server.permissions.permissions import UserIsAdmin
from server.serializer import JSendSchema, RentalSchema, JSendStatus
from server.serializer.decorators import returns
from server.service.rentals import get_rental_with_distance, get_rentals
from server.service.users import get_user
from server.views.base import BaseView
from server.views.utils import match_getter, GetFrom


class RentalsView(BaseView):
    """
    Gets a list of all rentals.
    """
    url = "/rentals"
    with_user = match_getter(get_user, 'user', firebase_id=GetFrom.AUTH_HEADER)

    @with_user
    @requires(UserIsAdmin())
    @returns(JSendSchema.of(RentalSchema(only=(
        "id", "user_id", "user_url", "bike_id",
        "bike_url", "start_time", "is_active"
    )), many=True))
    async def get(self, user):
        return {
            "status": JSendStatus.SUCCESS,
            "data": [
                await rental.serialize(self.rental_manager, self.request.app.router) for rental in await get_rentals()
            ]
        }


class RentalView(BaseView):
    """
    Gets or updates a single rental.
    """
    url = "/rentals/{id:[0-9]+}"
    with_rental = match_getter(get_rental_with_distance, 'rental', 'distance', target='id')
    with_user = match_getter(get_user, 'user', firebase_id=GetFrom.AUTH_HEADER)

    @with_rental
    @with_user
    @requires(UserIsAdmin())
    @returns(JSendSchema.of(RentalSchema(only=(
        "id", "user_id", "user_url", "bike_id", "bike_url",
        "start_time", "is_active", "distance"
    ))))
    async def get(self, rental: Rental, user, distance: float):
        return {
            "status": JSendStatus.SUCCESS,
            "data": await rental.serialize(self.rental_manager, self.request.app.router, distance=distance)
        }
