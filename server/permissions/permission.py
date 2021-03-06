"""
Permission
----------
"""

from abc import ABC, abstractmethod
from collections import defaultdict
from itertools import chain
from typing import List, Dict, Set

from aiohttp.web_urldispatcher import View


class RoutePermissionError(Exception):
    """
    Encapsulates a problem with permissions, and defines some
    useful functions to print them nicely.
    """

    def __init__(self, *messages, qualifier=None, sub_errors: List['RoutePermissionError'] = None):
        """
        :param sub_errors: Any additional sub-errors encountered.
        """

        if messages and (qualifier is not None or sub_errors is not None):
            raise ValueError("RoutePermissionError may either return a message or sub errors.")

        self.messages = messages
        self.sub_errors = sub_errors if sub_errors is not None else []
        self.qualifier = qualifier

    def __str__(self):
        """Prints a friendly description of the error.."""
        friendly_errors = [str(error) for error in self.sub_errors]
        if len(friendly_errors) > 1:
            friendly_errors[-1] = f"{self.qualifier} {friendly_errors[-1]}"
        friendly_errors = ", ".join(friendly_errors)

        messages = [m.lower().strip(".") for m in self.messages]
        return ", ".join(messages) + friendly_errors

    def serialize(self):
        """Appends the messages of an error to the messages of its sub-errors."""
        return list(self.messages) + list(chain.from_iterable(err.serialize() for err in self.sub_errors))


class Permission(ABC):
    """
    The base class for permissions. Implements the boolean logic.
    """

    def __and__(self, other):
        """Compose permissions using the "&" operator."""
        permissions = []
        for elem in (self, other):
            if isinstance(elem, AndPermission):
                permissions += elem._sub_permissions()
            else:
                permissions.append(elem)
        return AndPermission(*permissions)

    def __or__(self, other):
        """Compose permissions using the "|" operator."""
        permissions = []
        for elem in (self, other):
            if isinstance(elem, OrPermission):
                permissions += elem._sub_permissions()
            else:
                permissions.append(elem)
        return OrPermission(*permissions)

    def __invert__(self):
        """Negates the permission."""
        return NotPermission(self)

    def _sub_permissions(self):
        """Returns the sub-permissions."""
        return []

    @abstractmethod
    async def __call__(self, view: View, **kwargs) -> None:
        """
        Evaluates the permission object.

        :returns: None
        :raises RoutePermissionError: If the permission failed.
        """

    @property
    def openapi_security(self) -> List:
        """Returns the required OpenAPI security for the given path."""
        return []


class AndPermission(Permission):
    """Allows composing permissions together with the user of the ``&`` operator."""

    def __init__(self, *permissions):
        self._permissions = permissions

    async def __call__(self, view, **kwargs):
        errors = []

        for permission in self._permissions:
            try:
                await permission(view, **kwargs)
            except RoutePermissionError as error:
                errors.append(error)

        if errors:
            raise RoutePermissionError(qualifier="and", sub_errors=errors)

    def __repr__(self):
        return "(" + " & ".join(repr(p) for p in self._permissions) + ")"

    def __len__(self):
        return len(self._permissions)

    def _sub_permissions(self):
        return self._permissions

    @property
    def openapi_security(self) -> List:
        """.. note:: Not sure how this interacts with nested or..."""

        # we don't want duplicates
        security: Dict[str, Set[str]] = defaultdict(set)

        # get the security dictionary for each sub-permission
        security_entries = chain.from_iterable(permission.openapi_security for permission in self._permissions)

        # merge the list of security dictionaries into one
        for schema, securities in chain.from_iterable(entry.items() for entry in security_entries):
            security[schema] |= set(securities)

        return [{k: list(v) for k, v in security.items()}]


class OrPermission(Permission):
    """Allows composing permissions together with the use of the ``|`` operator."""

    def __init__(self, *permissions):
        self._permissions = permissions

    async def __call__(self, view, **kwargs):
        errors = []

        for permission in self._permissions:
            try:
                await permission(view, **kwargs)
                return
            except RoutePermissionError as error:
                errors.append(error)

        raise RoutePermissionError(qualifier="or", sub_errors=errors)

    def __repr__(self):
        return "(" + " | ".join(repr(p) for p in self._permissions) + ")"

    def __len__(self):
        return len(self._permissions)

    def _sub_permissions(self):
        return self._permissions

    @property
    def openapi_security(self):
        return list(chain.from_iterable(permission.openapi_security for permission in self._permissions))


class NotPermission(Permission):
    """
    Inverts a permission.

    .. todo:: Handle openapi "not" clauses
    """

    def __init__(self, permission):
        self._permission = permission

    async def __call__(self, view, **kwargs):
        try:
            await self._permission(view, **kwargs)
        except RoutePermissionError:
            return
        else:
            raise RoutePermissionError(f"Permission {self._permission} passed, but is inverted.")
