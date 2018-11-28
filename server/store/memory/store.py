from typing import Optional, Iterator, Dict

from server.models.bike import Bike
from server.store.persistent_store import PersistentStore


class MemoryStore(PersistentStore):
    """
    Emulates a database by doing all the operation in memory.
    """

    bikes: Dict[int, Bike] = {
        0: Bike(0, bytes.fromhex("f7fcc181b7f705501a40f74bd86161d9f403854bca9214d211d0a9f09fc904b6")),
        1: Bike(1, bytes.fromhex("3cfa82043bec8d96045782be8eedf900fe14e392ee5cd16c645ff69c2a8748ac")),
        2: Bike(2, bytes.fromhex("a3eb292b3b73452f8886d5c47b3936f7d8d3815d266fb3419322893e180364e9")),
        3: Bike(3, bytes.fromhex("8861b3d855f52fd9791a9204e1a6553de287abb3433acee66cc3064687455892")),
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
                if value.public_key == public_key
            }

        return iter(bikes.values())

    def get_bike(self, *, bike_id: Optional[int] = None,
                 public_key: Optional[bytes] = None) -> Optional[Bike]:
        bikes = self.get_bikes(bike_id=bike_id, public_key=public_key)
        return next(iter(bikes)) if bikes else None
