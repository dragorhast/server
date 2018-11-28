"""
Handles all the rentals CRUD.

To start a rental, go through the bike.
"""
from server.views.base import BaseView


class RentalsView(BaseView):
    """
    Gets a list of all active rentals.
    """
    url = "/rentals"

    async def get(self):
        pass


class RentalView(BaseView):
    """
    Gets or updates a single rental.
    """
    url = "/rentals/{id:[0-9]+}"

    async def get(self):
        pass
