from aiohttp.web_urldispatcher import View

from server.models import User, Bike, Reservation
from server.permissions.permission import RoutePermissionError, Permission
from server.service.access.users import get_user
from server.service.verify_token import verify_token, TokenVerificationError


class UserIsAdmin(Permission):
    """Asserts that a given user is an admin."""

    async def __call__(self, view: View, user: User, **kwargs):
        if "token" not in view.request:
            raise RoutePermissionError("No firebase jwt was included in the Authorization header. (1001)")

        if not view.request["token"] == user.firebase_id:
            # an admin is fetching a user's details; we need to get the admin's details
            user = await get_user(firebase_id=view.request["token"])

        if user is None or not user.is_admin:
            raise RoutePermissionError("The supplied token doesn't have admin rights.")

    @property
    def openapi_security(self):
        return [{"FirebaseToken": ["admin"]}]


class UserOwnsReservation(Permission):
    """Assert that a user owns the given reservation."""

    async def __call__(self, view: View, user: User, reservation: Reservation):
        if not reservation.user_id == user.id:
            raise RoutePermissionError("The supplied token did not make this reservation.")


class UserIsRentingBike(Permission):
    """Asserts that the given user is renting the given bike."""

    async def __call__(self, view: View, user: User, bike: Bike, **kwargs):
        if not view.rental_manager.is_renting(user.id, bike.id):
            raise RoutePermissionError("The supplied token does not have an active rental for this bike.")

    @property
    def openapi_security(self):
        return [{"FirebaseToken": ["user"]}]


class UserMatchesToken(Permission):
    """Asserts that the given user matches the firebase id."""

    async def __call__(self, view: View, user: User, **kwargs):
        if "token" not in view.request:
            raise RoutePermissionError("No firebase jwt was included in the Authorization header. (1000)")
        else:
            token = view.request["token"]

        if not user.firebase_id == token:
            raise RoutePermissionError("The supplied token doesn't have access to this resource.")

    @property
    def openapi_security(self):
        return [{"FirebaseToken": ["user"]}]


class ValidToken(Permission):
    """Asserts that the request has a valid firebase token."""

    async def __call__(self, view: View, **kwargs):
        try:
            token = verify_token(view.request)
        except TokenVerificationError as error:
            raise RoutePermissionError(error.message)
        else:
            view.request["token"] = token
