from nacl.signing import SigningKey, SignedMessage


class Bike:
    bid: int
    seed: bytes
    locked: bool

    def __init__(self, bid, seed, locked=False):
        self.bid = bid
        self.seed = seed
        self.signing_key = SigningKey(seed)
        self.locked = locked
        self.commands = {
            "lock": self.lock,
            "unlock": self.unlock,
        }

    @property
    def public_key(self):
        return self.signing_key.verify_key

    def sign(self, data) -> SignedMessage:
        return self.signing_key.sign(data)

    async def lock(self, msg, socket):
        self.locked = True
        await socket.send_str("locked")

    async def unlock(self, msg, socket):
        self.locked = False
        await socket.send_str("unlocked")
