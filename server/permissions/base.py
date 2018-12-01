from abc import ABC, abstractmethod

from server.permissions.user import User


class Permission(ABC):
    """
    The base class for permissions. Implements the boolean logic.
    """

    @abstractmethod
    def __and__(self, other):
        """Compose permissions using the "&" operator."""

    @abstractmethod
    def __or__(self, other):
        """Compose permissions using the "|" operator."""

    @abstractmethod
    def __invert__(self):
        """Negates the permission."""

    @abstractmethod
    def check(self, user: User):
        pass
