"""
Permissions
-----------

This module contains the various permission types. A permission is essentially
just an object (either function or class) that can be called asynchronously
and raises a PermissionError in the case of a failed permission.
"""

from aiohttp.web_urldispatcher import View

from server.models import User
from server.permissions.permission import Permission
from server.service.verify_token import verify_token, TokenVerificationError


class ValidToken(Permission):
    """Asserts that the request has a valid firebase token."""

    async def __call__(self, view: View, **kwargs):
        try:
            token = verify_token(view.request)
        except TokenVerificationError as error:
            raise PermissionError(*error.args)
        else:
            view.request["token"] = token


class UserMatchesFirebase(Permission):
    """Asserts that the given user matches the firebase id."""

    async def __call__(self, view: View, **kwargs):
        if "token" not in view.request:
            raise PermissionError("You must supply your firebase token.")
        else:
            token = view.request["token"]

        if "user" in kwargs:
            user = kwargs["user"]
        else:
            raise ValueError(
                "User required for this permission! "
                "It is recommended you cache it on the request using a match_getter"
            )

        if not user.firebase_id == token:
            raise PermissionError("You don't have permission to fetch this resource.")


class UserIsAdmin(Permission):
    """Asserts that a given user is an admin."""

    async def __call__(self, view: View, **kwargs):
        if "token" not in view.request:
            raise PermissionError("You must supply your firebase token.")

        if "user" in kwargs:
            user = kwargs["user"]
        else:
            raise ValueError(
                "User required for this permission! "
                "It is recommended you cache it on the request using a match_getter"
            )

        if not user.is_admin:
            raise PermissionError("You don't have permission to fetch this resource.")


class BikeNotInUse(Permission):
    """Asserts that the given bike is not being used."""

    async def __call__(self, view: View, **kwargs):
        if "bike" not in kwargs:
            raise ValueError("Bike required for this permission! Maybe you didn't include a getter before it?")
        else:
            bike = kwargs["bike"]

        if await view.request.app["rental_manager"].bike_in_use(bike):
            raise PermissionError("The requested bike is in use.")
