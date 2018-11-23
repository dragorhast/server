from typing import Optional, List, Union, Iterator

from server.store.models.bike import Bike
from server.store.store import Store


class MemoryStore(Store):
    """
    Emulates a database by doing all the operation in memory.
    """

    bikes = {
        0: Bike(0, b'\xf7\xfc\xc1\x81\xb7\xf7\x05P\x1a@\xf7K\xd8aa\xd9\xf4\x03\x85K\xca\x92\x14\xd2\x11\xd0\xa9\xf0\x9f\xc9\x04\xb6')
    }

    def get_bikes(self, *, bike_id: Optional[int] = None) -> Union[Iterator[Bike], Optional[Bike]]:
        if bike_id is not None:
            return self.bikes[bike_id].serialize() if bike_id in self.bikes else None
        else:
            return (bike.serialize() for bike in self.bikes.values())
