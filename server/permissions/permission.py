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
    async def __call__(self, view: View, **kwargs) -> None:
        """
        Evaluates the permission object.

        :returns: None
        :raises PermissionError: If the permission failed.
        """


class AndPermission(Permission):

    def __init__(self, *permissions):
        self._permissions = permissions

    async def __call__(self, view, **kwargs):
        errors = []

        for permission in self._permissions:
            try:
                await permission(view, **kwargs)
            except PermissionError as error:
                errors.append(error)

        if errors:
            raise PermissionError(*errors)

    def __repr__(self):
        return "(" + " & ".join(repr(p) for p in self._permissions) + ")"


class OrPermission(Permission):

    def __init__(self, *permissions):
        self._permissions = permissions

    async def __call__(self, view, **kwargs):
        errors = []

        for permission in self._permissions:
            try:
                await permission(view, **kwargs)
                return
            except PermissionError as error:
                errors.append(error)

        raise PermissionError(*errors)

    def __repr__(self):
        return "(" + " | ".join(repr(p) for p in self._permissions) + ")"


class NotPermission(Permission):

    def __init__(self, permission):
        self._permission = permission

    async def __call__(self, view, **kwargs):
        try:
            await self._permission(view, **kwargs)
        except PermissionError:
            return
        else:
            raise PermissionError(f"Permission {self._permission} passed, but is inverted.")
