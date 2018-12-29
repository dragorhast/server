from abc import ABC

from server.permissions.base import Permission
from server.token_verify import verify_token


class UserPermission(Permission, ABC):

    async def __call__(self, view, user):
        pass


class AuthenticatedPermission(UserPermission):

    async def __call__(self, view, user):
        token = verify_token(view.request)

        if not user.firebase_id == token:
            raise PermissionError("You don't have permission to fetch this resource.")


class AdminPermission(UserPermission):

    async def __call__(self, view, user):
        return "127.0.0.1" in view.request.remote
