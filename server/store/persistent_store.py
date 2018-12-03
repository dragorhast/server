"""
This module hosts the abstract base class for all persistent storage.
This class is used to define the "contract" that all storage backends
must adhere to. Any class that implements this interface is assumed to
provide a persistent data store.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Iterator

from server.models.bike import Bike
from server.models.rental import Rental
from server.models.user import User


class PersistentStore(ABC):
    """The abstract store interface."""

    @abstractmethod
    async def get_bikes(self, *,
                        bike_id: Optional[int] = None,
                        public_key: Optional[bytes] = None) -> Iterator[Bike]:
        """
        Gets bikes that match the given filters.
        """

    @abstractmethod
    async def get_bike(self, *, bike_id: Optional[int] = None,
                       public_key: Optional[bytes] = None) -> Optional[Bike]:
        """
        Gets a single bike that matches the given filters.
        """

    @abstractmethod
    async def add_bike(self, public_key) -> Bike:
        """Adds a bike to the system."""

    @abstractmethod
    async def get_users(self) -> Iterator[User]:
        """Gets all users."""

    @abstractmethod
    async def get_rentals(self, *, bike_id: Optional[int] = None) -> Iterator[Rental]:
        """Gets all rentals."""

    @abstractmethod
    async def add_rental(self, user_id, bike_id):
        """Adds a new rental."""
