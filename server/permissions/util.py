from functools import wraps
from itertools import chain

from aiohttp import web
from aiohttp.web_urldispatcher import View

from server.models import User
from server.permissions import Permission
from server.permissions.auth import UserPermission
from server.serializer import JSendSchema, JSendStatus


def require_user_permission(permission: UserPermission):
    if not isinstance(permission, Permission):
        raise TypeError

    def decorator(original_function):

        @wraps(original_function)
        async def new_func(self: View, user: User):
            errors = []

            try:
                await permission(self, user)
            except PermissionError as e:
                errors.append(e)

            if errors:
                response_schema = JSendSchema()
                return web.json_response(response_schema.dump({
                    "status": JSendStatus.FAIL,
                    "data": {"authorization": list(chain.from_iterable(error.args for error in errors))}
                }), status=401)

            return await original_function(self, user)

        return new_func

    return decorator
