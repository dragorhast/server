"""
Rental Related Views
---------------------------

Handles all the rentals CRUD.

To start a rental, go through the bike.
"""
from server.models import Rental
from server.serializer import JSendSchema, RentalSchema, JSendStatus
from server.serializer.decorators import returns
from server.service.rentals import get_rental
from server.views.base import BaseView
from server.views.utils import getter


class RentalsView(BaseView):
    """
    Gets a list of all active rentals.
    """
    url = "/rentals"

    @returns(JSendSchema.of(RentalSchema(), many=True))
    async def get(self):
        return {
            "status": JSendStatus.SUCCESS,
            "data": [await rental.serialize(self.request.app["rental_manager"]) for rental in
                     await self.request.app["rental_manager"].active_rentals()]
        }


class RentalView(BaseView):
    """
    Gets or updates a single rental.
    """
    url = "/rentals/{id:[0-9]+}"
    with_rental = getter(get_rental, 'id', 'rental_id', 'rental')

    @with_rental
    @returns(JSendSchema.of(RentalSchema()))
    async def get(self, rental: Rental):
        return {
            "status": JSendStatus.SUCCESS,
            "data": await rental.serialize(self.request.app["rental_manager"])
        }
