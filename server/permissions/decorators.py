"""
Decorators
----------
"""

from functools import wraps
from http import HTTPStatus

from aiohttp import web
from aiohttp.web_urldispatcher import View

from server.permissions.permission import RoutePermissionError, Permission
from server.serializer import JSendSchema, JSendStatus


def requires(permission: Permission):
    """A decorator that requires the given permission to be met to continue."""

    if not isinstance(permission, Permission):
        raise TypeError

    def decorator(original_function):

        @wraps(original_function)
        async def new_func(self: View, **kwargs):
            try:
                await permission(self, **kwargs)
            except RoutePermissionError as error:
                response_schema = JSendSchema()
                return web.json_response(response_schema.dump({
                    "status": JSendStatus.FAIL,
                    "data": {
                        "message": f"You cannot do that because because {str(error)}.",
                        "reasons": error.serialize()
                    }
                }), status=HTTPStatus.UNAUTHORIZED)
            except Exception as error:
                raise type(error)(original_function, *error.args) from error

            return await original_function(self, **kwargs)

        return new_func

    return decorator
