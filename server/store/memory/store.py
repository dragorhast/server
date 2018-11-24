from typing import Optional, Union, Iterator, Dict

from server.models.bike import Bike
from server.store.store import Store


class MemoryStore(Store):
    """
    Emulates a database by doing all the operation in memory.
    """

    bikes: Dict[int, Bike] = {
        0: Bike(0,
                b'\xf7\xfc\xc1\x81\xb7\xf7\x05P\x1a@\xf7K\xd8aa\xd9\xf4\x03\x85K\xca\x92\x14\xd2\x11\xd0\xa9\xf0\x9f\xc9\x04\xb6')
    }

    def get_bikes(self, *,
                  bike_id: Optional[int] = None,
                  public_key: Optional[bytes] = None) -> Iterator[Bike]:

        bikes = self.bikes

        if bike_id is not None:
            bikes = {
                key: value
                for key, value
                in bikes.items()
                if key == bike_id
            }

        if public_key is not None:
            bikes = {
                key: value
                for key, value
                in bikes.items()
                if value.pub == public_key
            }

        return bikes.values()

    def get_bike(self, bike_id: Optional[int] = None,
                 public_key: Optional[bytes] = None) -> Optional[Bike]:
        bikes = self.get_bikes(bike_id=bike_id, public_key=public_key)
        return next(iter(bikes)) if bikes else None
