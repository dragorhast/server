from typing import Optional

from server.store.persistent_store import PersistentStore


class PostgresStore(PersistentStore):

    def get_bike(self, *, bike_id: Optional[int] = None, public_key: Optional[bytes] = None):
        pass

    def get_bikes(self, *, bike_id: Optional[int] = None, public_key: Optional[bytes] = None):
        pass
