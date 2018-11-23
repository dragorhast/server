"""
Handles all the user CRUD
"""
from aiohttp import web

from server.views.base import BaseView


class UsersView(BaseView):
    """
    Gets or adds to the list of users.
    """
    url = "/users"
    cors_allowed = True

    async def get(self):
        return web.json_response([])

    async def post(self):
        pass


class UserView(BaseView):
    """
    Gets, updates or deletes a single user.
    """
    url = "/users/{id}"
    cors_allowed = True

    async def get(self):
        pass

    async def delete(self):
        pass

    async def patch(self):
        pass


class UserRentalsView(BaseView):
    """
    Gets or adds to the users list of rentals.
    """
    url = "/users/{id}/rentals"

    async def get(self):
        pass

    async def post(self):
        pass


class UserReservationsView(BaseView):
    """
    Gets or adds to the users' list of reservations.
    """
    url = "/users/{id}/reservations"

    async def get(self):
        pass

    async def post(self):
        pass


class UserIssuesView(BaseView):
    """
    Gets or adds to the users' list of issues.
    """
    url = "/users/{id}/issues"

    async def get(self):
        pass

    async def post(self):
        pass


class MeView(BaseView):
    """
    Gets the data for the currently authenticated user/
    """
    pass
