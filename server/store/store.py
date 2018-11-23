from abc import ABC, abstractmethod
from typing import Optional


class Store(ABC):

    @abstractmethod
    def get_bikes(self, *, bike_id: Optional[int] = None):
        """
        Gets bikes that match the given filters.
        """
        pass

