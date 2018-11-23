from typing import Optional

from server.store.store import Store


class MemoryStore(Store):
    bikes = [{
        "id": 0,
        "pub": b'\xf7\xfc\xc1\x81\xb7\xf7\x05P\x1a@\xf7K\xd8aa\xd9\xf4\x03\x85K\xca\x92\x14\xd2\x11\xd0\xa9\xf0\x9f\xc9\x04\xb6'
    }]

    def get_bikes(self, *, bike_id: Optional[int] = None):
        return self.bikes if bike_id is None else self.bikes[bike_id]
