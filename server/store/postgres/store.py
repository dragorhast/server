from typing import Optional

from server.store.store import Store


class PostgresStore(Store):

    def get_bikes(self, *, bike_id: Optional[int] = None):
        pass