from functools import wraps
from typing import List

from aiohttp import web
from aiohttp.web_urldispatcher import View

from server.permissions import Permission
from server.serializer import JSendSchema, JSendStatus


def flatten(permission_error) -> List[str]:
    elements: List[str] = []

    for arg in permission_error.args:
        if isinstance(arg, PermissionError):
            elements += flatten(arg)
        else:
            elements.append(arg)

    return elements


def requires(permission: Permission):
    """A decorator that requires the given permission to be met to continue."""

    if not isinstance(permission, Permission):
        raise TypeError

    def decorator(original_function):

        @wraps(original_function)
        async def new_func(self: View, **kwargs):
            errors: List[str] = []

            try:
                await permission(self, **kwargs)
            except PermissionError as error:
                errors += flatten(error)

            if errors:
                response_schema = JSendSchema()
                return web.json_response(response_schema.dump({
                    "status": JSendStatus.FAIL,
                    "data": {"authorization": errors}
                }), status=401)

            return await original_function(self, **kwargs)

        return new_func

    return decorator
