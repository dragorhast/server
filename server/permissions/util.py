from functools import wraps

from aiohttp import web
from aiohttp.web_urldispatcher import View

from server.permissions.base import Permission


def require_permission(permission: Permission):
    def require_permission(original_function):
        @wraps(original_function)
        async def new_func(self: View):
            passed = await permission(self.request, self)
            if not passed:
                raise web.HTTPForbidden(reason="You don't possess the required credentials.")
            return await original_function(self)

        return new_func

    return require_permission
