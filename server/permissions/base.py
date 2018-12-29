from abc import ABC, abstractmethod

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
    async def __call__(self, view: View, *args) -> bool:
        """
        Evaluates the permission object.

        :returns: None
        :raises PermissionError: If the permission failed.
        """


class AndPermission(Permission):

    def __init__(self, *permissions):
        self._permissions = permissions

    async def __call__(self, view, *args):
        errors = []

        for permission in self._permissions:
            try:
                await permission(view, *args)
            except PermissionError as e:
                errors.append(e)

        if errors:
            raise PermissionError(*errors)

        return True

    def __repr__(self):
        return "(" + " & ".join(repr(p) for p in self._permissions) + ")"


class OrPermission(Permission):

    def __init__(self, *permissions):
        self._permissions = permissions

    async def __call__(self, view, *args):
        errors = []

        for permission in self._permissions:
            try:
                await permission(view, *args)
                return True
            except PermissionError as e:
                errors.append(e)

        raise PermissionError(*errors)

    def __repr__(self):
        return "(" + " | ".join(repr(p) for p in self._permissions) + ")"


class NotPermission(Permission):

    def __init__(self, permission):
        self._permission = permission

    async def __call__(self, view, *args):
        return not self._permission(view, *args)
