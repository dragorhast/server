from abc import ABC, abstractmethod

from aiohttp.web_request import Request
from aiohttp.web_urldispatcher import View


class Permission(ABC):
    """
    The base class for permissions. Implements the boolean logic.
    """

    def __and__(self, other):
        """Compose permissions using the "&" operator."""
        return AndPermission(self, other)

    def __or__(self, other):
        """Compose permissions using the "|" operator."""
        return OrPermission(self, other)

    def __invert__(self):
        """Negates the permission."""
        return NotPermission(self)

    @abstractmethod
    async def __call__(self, request: Request, view: View) -> bool:
        """Evaluates the permission object."""


class AndPermission(Permission):

    def __init__(self, *permissions):
        self._permissions = permissions

    async def __call__(self, request, view):
        return all([await permission(request, view) for permission in self._permissions])

    def __repr__(self):
        return "(" + " & ".join(repr(p) for p in self._permissions) + ")"


class OrPermission(Permission):

    def __init__(self, *permissions):
        self._permissions = permissions

    async def __call__(self, request, view):
        return any([await permission(request, view) for permission in self._permissions])

    def __repr__(self):
        return "(" + " | ".join(repr(p) for p in self._permissions) + ")"


class NotPermission(Permission):

    def __init__(self, permission):
        self._permission = permission

    async def __call__(self, request, view):
        return not self._permission(request, view)
