from attr import dataclass


@dataclass
class Bike:

    bid: int
    pub: bytes

    def serialize(self):
        return {
            "id": self.bid,
            "pub": self.pub.hex()
        }
