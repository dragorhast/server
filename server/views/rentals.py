"""
Rental Related Views
---------------------------

Handles all the rentals CRUD.

To start a rental, go through the bike.
"""
from aiohttp_apispec import docs

from server.models import Rental
from server.permissions.decorators import requires
from server.permissions.users import UserIsAdmin
from server.serializer import JSendSchema, JSendStatus
from server.serializer.decorators import returns
from server.serializer.fields import Many
from server.serializer.models import RentalSchema
from server.service.access.rentals import get_rental_with_distance, get_rentals
from server.service.access.users import get_user
from server.views.base import BaseView
from server.views.decorators import match_getter, GetFrom, Optional


class RentalsView(BaseView):
    """
    Gets a list of all rentals.
    """
    url = "/rentals"
    name = "rentals"
    with_user = match_getter(get_user, 'user', firebase_id=GetFrom.AUTH_HEADER)

    @with_user
    @docs(summary="Get All Rentals")
    @requires(UserIsAdmin())
    @returns(JSendSchema.of(
        rentals=Many(RentalSchema(only=(
            "id", "user_id", "user_url", "bike_identifier",
            "bike_url", "start_time", "is_active"
        )))
    ))
    async def get(self, user):
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"rentals": [
                await rental.serialize(self.rental_manager, self.bike_connection_manager, self.request.app.router)
                for rental in await get_rentals()
            ]}
        }


class RentalView(BaseView):
    """
    Gets or updates a single rental.
    """
    url = "/rentals/{id}"
    name = "rental"
    with_rental = match_getter(get_rental_with_distance, 'rental', Optional('distance'), target='id')
    with_user = match_getter(get_user, 'user', firebase_id=GetFrom.AUTH_HEADER)

    @with_rental
    @with_user
    @docs(summary="Get A Rental")
    @requires(UserIsAdmin())
    @returns(JSendSchema.of(rental=RentalSchema(only=(
        "id", "user_id", "user_url", "bike_identifier", "bike_url",
        "start_time", "is_active", "distance"
    ))))
    async def get(self, rental: Rental, user, distance: float):
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"rental": await rental.serialize(
                self.rental_manager, self.bike_connection_manager, self.request.app.router, distance=distance
            )}
        }
