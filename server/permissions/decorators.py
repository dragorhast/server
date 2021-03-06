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


def add_apispec_permission(original_function, new_func, permission):
    """Set up the apispec documentation on the new function"""
    if hasattr(original_function, "__apispec__"):
        new_func.__apispec__ = original_function.__apispec__
    else:
        new_func.__apispec__ = {"responses": {}, "parameters": []}

    if "security" not in new_func.__apispec__:
        new_func.__apispec__["security"] = []

    new_func.__apispec__["security"].extend(permission.openapi_security)


def requires(permission: Permission):
    """A decorator that requires the given permission to be met to continue."""

    if not isinstance(permission, Permission):
        raise TypeError

    def decorator(original_function):

        @wraps(original_function)
        async def new_func(self: View, **kwargs):
            """Checks the given request against the supplied permission and gracefully fails."""
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

        add_apispec_permission(original_function, new_func, permission)

        return new_func

    return decorator
