"""
Handles all the reservations CRUD

To create a new reservation, go through the pickup point.
"""
from server.views.base import BaseView


class ReservationsView(BaseView):
    """
    Gets the list of reservations.
    """
    url = "/reservations"

    async def get(self):
        pass


class ReservationView(BaseView):
    """
    Gets or updates a single reservation.
    """
    url = "/reservations/{id}"

    async def get(self):
        pass

    async def patch(self):
        pass
