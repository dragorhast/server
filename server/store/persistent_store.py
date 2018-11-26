"""
This module hosts the abstract base class for all persistent storage.
This class is used to define the "contract" that all storage backends
must adhere to. Any class that implements this interface is assumed to
provide a persistent data store.
"""

from abc import ABC, abstractmethod
from typing import Optional

from server.models.bike import Bike


class PersistentStore(ABC):
    """The abstract store interface."""

    @abstractmethod
    def get_bikes(self, *, bike_id: Optional[int] = None):
        """
        Gets bikes that match the given filters.
        """
        pass

    @abstractmethod
    def get_bike(self, *, bike_id: Optional[int] = None,
                 public_key: Optional[bytes] = None) -> Optional[Bike]:
        """
        Gets a single bike that matches the given filters.
        """
        pass
