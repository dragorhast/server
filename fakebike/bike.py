from nacl.signing import SigningKey


class Bike:
    seed: bytes
    locked: bool = False

    def __init__(self, seed):
        self.seed = seed
        self.signing_key = SigningKey(seed)
        self.commands = {
            "lock": self.lock,
            "unlock": self.unlock,
        }

    @property
    def public_key(self):
        return self.signing_key.verify_key

    def sign(self, data):
        return self.signing_key.sign(data)

    async def lock(self, msg, socket):
        self.locked = True
        await socket.send_str("locked")

    async def unlock(self, msg, socket):
        self.locked = False
        await socket.send_str("unlocked")
