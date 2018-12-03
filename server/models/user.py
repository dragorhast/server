from dataclasses import dataclass


@dataclass
class User:
    uid: int
    first: str
    last: str

    def serialize(self):
        return {
            "id": self.uid,
            "first": self.first,
            "last": self.last
        }
