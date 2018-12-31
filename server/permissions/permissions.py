from aiohttp.web_urldispatcher import View

from server.permissions import Permission
from server.service.verify_token import verify_token, TokenVerificationError


class ValidToken(Permission):
    """Asserts that the request has a valid firebase token."""

    async def __call__(self, view: View, **kwargs):
        try:
            token = verify_token(view.request)
        except TokenVerificationError as e:
            raise PermissionError(*e.args)
        else:
            view.request["token"] = token


class UserMatchesFirebase(Permission):
    """Asserts that the given user matches the firebase id."""

    async def __call__(self, view: View, **kwargs):
        if "user" not in kwargs:
            raise ValueError("User required for this permission! Maybe you didn't include a getter before it?")
        else:
            user = kwargs["user"]

        if "token" not in view.request:
            raise PermissionError("You must supply your firebase token.")
        else:
            token = view.request["token"]

        if not user.firebase_id == token:
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
