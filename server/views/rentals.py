"""
Rental Related Views
---------------------------

Handles all the rentals CRUD.

To start a rental, go through the bike.
"""

from server.models import Rental
from server.serializer import JSendSchema, RentalSchema, JSendStatus
from server.serializer.decorators import returns
from server.service.rentals import get_rental_with_distance, get_rentals
from server.views.base import BaseView
from server.views.utils import match_getter


class RentalsView(BaseView):
    """
    Gets a list of all active rentals.
    """
    url = "/rentals"

    @returns(JSendSchema.of(RentalSchema(only=("id", "user_id", "user_url", "bike_id", "bike_url", "start_time", "is_active")), many=True))
    async def get(self):
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

    @with_rental
    @returns(JSendSchema.of(
        RentalSchema(only=("id", "user_id", "user_url", "bike_id", "bike_url", "start_time", "is_active", "distance"))))
    async def get(self, rental: Rental, distance: float):
        return {
            "status": JSendStatus.SUCCESS,
            "data": await rental.serialize(self.rental_manager, self.request.app.router,
                                           distance=distance)
        }
