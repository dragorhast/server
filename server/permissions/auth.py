from json import JSONDecodeError

from server.permissions.base import Permission


class AuthenticatedPermission(Permission):

    async def __call__(self, request, view):
        try:
            data = await request.json()
        except JSONDecodeError:
            return False
        else:
            return "auth" in data


class AdminPermission(Permission):

    async def __call__(self, request, view):
        return "127.0.0.1" in request.remote
