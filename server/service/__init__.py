"""
The service layer for the system. Acts as the internal API.
Each interface (REST API, web-sockets) should use the
service layer to implement their logic.

The service layer implements the use cases for the system.
"""
from typing import Optional, Union, Iterable

from server.models import Bike, User, RentalUpdate, RentalUpdateType


async def get_bikes():
    """Gets all the bikes from the system."""
    return await Bike.get()


async def get_bike(*, bike_id: Optional[int] = None,
                   public_key: Optional[bytes] = None):
    """Gets a bike from the system."""
    return await Bike.get(id=bike_id, public_key_hex=public_key.hex()).first()


async def create_bike(public_key: Union[str, bytes]) -> Bike:
    """
    Creates a bike and returns it.

    :param public_key: The public key, or a string hex representation of it.
    :raises ValueError: If the key is not hex string
    """

    if not isinstance(public_key, str) or isinstance(public_key, bytes):
        raise TypeError

    if isinstance(public_key, str):
        try:
            public_key = bytes.fromhex(public_key)
        except ValueError:
            raise ValueError("Key is not a hex string!")

    existing = await store.get_bike(public_key=public_key)
    if existing is not None:
        return existing

    return await store.add_bike(public_key)


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
