"""
The service layer for the system. Acts as the internal API.
Each interface (REST API, web-sockets) should use the
service layer to implement their logic.

The service layer implements the use cases for the system.
"""
from typing import Optional, Union

from tortoise.exceptions import DoesNotExist

from server.models import Bike, User, RentalUpdate, RentalUpdateType

MASTER_KEY = 0xdeadbeef.to_bytes(4, "big")


async def get_bikes():
    """Gets all the bikes from the system."""
    return await Bike.all()


async def get_bike(*, bike_id: Optional[int] = None,
                   public_key: Optional[bytes] = None) -> Optional[Bike]:
    """Gets a bike from the system."""
    kwargs = {}

    if bike_id:
        kwargs["id"] = bike_id
    if public_key:
        kwargs["public_key_hex"] = public_key.hex()

    try:
        return await Bike.get(**kwargs).first()
    except DoesNotExist:
        return None


class BadKeyException(Exception):
    pass


async def register_bike(public_key: Union[str, bytes], master_key: Union[str, bytes]) -> Bike:
    """
    Register a bike with the system, and return it.

    :param public_key: The public key, or a string hex representation of it.
    :param master_key: The master key, or a string hex representation of it.
    :raises TypeError: if the key is not the right type
    :raises ValueError: If the key is not hex string
    :raises BadKeyException: If the master key is not correct
    """

    keys = {
        "pub": public_key,
        "master": master_key
    }

    # check keys for type and convert to bytes
    for name, value in keys.items():
        if not isinstance(value, str) and not isinstance(value, bytes):
            raise TypeError("%s has incorrect type %s", name, type(value))

        if isinstance(value, str):
            try:
                keys[name] = bytes.fromhex(value)
            except ValueError:
                raise ValueError("Public key is not a hex string!")

    if not master_key == MASTER_KEY:
        raise BadKeyException

    existing = await get_bike(public_key=keys["pub"])

    if existing is not None:
        return existing

    return await Bike.create(public_key_hex=keys["pub"].hex())


async def lock_bike(public_key, value):
    """
    Locks or unlocks the bike with a public key.

    :param public_key: The key for the bike.
    :param value: The locked or unlocked value.
    :return: True if successful.
    :raises Exception: If the bike is not connected.
    """
    bike: Bike = Bike.get(public_key_hex=public_key.hex()).first()
    if not bike._is_connected:
        raise Exception

    await bike.set_locked(value)
    return True


async def get_users():
    return await User.get()


async def get_rentals(bike: Union[int, Bike]):
    """
    Gets rentals for a given bike.

    :param bike: The bike or id to fetch.
    :return: An iterable of rentals.

    todo: Properly determine all rentals and maybe cache.
    """
    if isinstance(bike, Bike):
        bid = bike.bid
    elif isinstance(bike, int):
        bid = bike
    else:
        raise TypeError("Must be bike id or bike.")

    return await RentalUpdate.get()


async def start_rental(bike, user):
    """

    :param bike:
    :param user:
    :return:

    todo: implement
    """
    update = RentalUpdate(user, bike, RentalUpdateType.RENT)


async def get_user() -> User:
    """

    :return:

    todo: implement
    """
    return await User.get().first()
