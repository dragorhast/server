"""
Handles all the pick-up point CRUD

- Customer can reserve a bike from a rack
- Admin must be able to get bikes in use / available at each location
"""

from server.views.base import BaseView


class PickupsView(BaseView):
    """
    Gets or adds to the list of all pick-up points.
    """
    url = "/pickups"

    async def get(self):
        pass

    async def post(self):
        pass


class PickupView(BaseView):
    """
    Gets, updates or deletes a single pick-up point.
    """
    url = "/pickups/{id:[0-9]+}"

    async def get(self):
        pass

    async def delete(self):
        pass

    async def patch(self):
        pass


class PickupBikesView(BaseView):
    """
    Gets list of bikes currently at a pickup point.
    """
    url = "/pickups/{id:[0-9]+}/bikes"

    async def get(self):
        pass


class PickupReservationsView(BaseView):
    """
    Gets or adds to a pickup point's list of reservations.
    """
    url = "/pickups/{id:[0-9]+}/reservations"

    async def get(self):
        pass

    async def post(self):
        pass
