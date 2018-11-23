"""
This module hosts the base class for all Stores.
A store must implement all function to be usable.
"""

from abc import ABC, abstractmethod
from typing import Optional


class Store(ABC):
    """The abstract store interface."""

    @abstractmethod
    def get_bikes(self, *, bike_id: Optional[int] = None):
        """
        Gets bikes that match the given filters.
        """
        pass
