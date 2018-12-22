from random import getrandbits


def random_key(size):
    return bytes(getrandbits(8) for _ in range(size)).hex()