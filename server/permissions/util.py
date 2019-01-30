from aiohttp.web_urldispatcher import View

from server.permissions.permission import RoutePermissionError, Permission
from server.service.verify_token import verify_token, TokenVerificationError


class ValidToken(Permission):
    """Asserts that the request has a valid firebase token."""

    async def __call__(self, view: View, **kwargs):
        try:
            token = verify_token(view.request)
        except TokenVerificationError as error:
            raise RoutePermissionError(error.message)
        else:
            view.request["token"] = token
