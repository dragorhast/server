from aiohttp.web_urldispatcher import View

from server.models import User, Bike
from server.permissions.permission import RoutePermissionError, Permission
from server.service.users import get_user


class UserIsAdmin(Permission):
    """Asserts that a given user is an admin."""

    async def __call__(self, view: View, user: User, **kwargs):
        if "token" not in view.request:
            raise RoutePermissionError("Please include your firebase jwt in the Authorization header. (1001)")

        if not view.request["token"] == user.firebase_id:
            # an admin is fetching a user's details; we need to get the admin's details
            user = await get_user(firebase_id=view.request["token"])

        if user is None or not user.is_admin:
            raise RoutePermissionError("The supplied token doesn't have admin rights.")


class UserIsRentingBike(Permission):
    """Asserts that the given user is renting the given bike."""

    async def __call__(self, view: View, user: User, bike: Bike, **kwargs):
        if not view.rental_manager.is_renting(user.id, bike.id):
            raise RoutePermissionError("The supplied token does not have an active rental for this bike.")


class UserMatchesFirebase(Permission):
    """Asserts that the given user matches the firebase id."""

    async def __call__(self, view: View, user: User, **kwargs):
        if "token" not in view.request:
            raise RoutePermissionError("Please include your firebase jwt in the Authorization header. (1000)")
        else:
            token = view.request["token"]

        if not user.firebase_id == token:
            raise RoutePermissionError("The supplied token doesn't have access to this resource.")
