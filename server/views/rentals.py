"""
Handles all the rentals CRUD.

To start a rental, go through the bike.
"""
from aiohttp import web

from server.serializer import JSendSchema, RentalSchema, JSendStatus
from server.views.base import BaseView


class RentalsView(BaseView):
    """
    Gets a list of all active rentals.
    """
    url = "/rentals"

    async def get(self):
        response_schema = JSendSchema.of(RentalSchema(), many=True)
        response_data = response_schema.dump({
            "status": JSendStatus.SUCCESS,
            "data": (rental.serialize() for rental in await self.request.app["rental_manager"].active_rentals())
        })

        return web.json_response(response_data)


class RentalView(BaseView):
    """
    Gets or updates a single rental.
    """
    url = "/rentals/{id:[0-9]+}"

    async def get(self):
        pass
