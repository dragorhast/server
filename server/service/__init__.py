"""
The service layer for the system. Acts as the internal API.
Each interface (REST API, web-sockets) should use the
service layer to implement their logic.

The service layer implements the use cases for the system.
"""
from typing import Optional, Union, Iterable, Any, Dict

from tortoise.exceptions import DoesNotExist

from server.models import Bike, User, RentalUpdate, RentalUpdateType

MASTER_KEY = 0xdeadbeef.to_bytes(4, "big")


async def get_bikes() -> Iterable[Bike]:
    """Gets all the bikes from the system."""
    return await Bike.all()


async def get_bike(*, bike_id: Optional[int] = None,
                   public_key: Optional[bytes] = None) -> Optional[Bike]:
    """Gets a bike from the system."""
    kwargs: Dict = {}

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

    def clean_key(name, key) -> bytes:
        if not isinstance(key, str) and not isinstance(key, bytes):
            raise TypeError(f"{name} has incorrect type {type(key)}")

        if isinstance(key, str):
            try:
                return bytes.fromhex(key)
            except ValueError:
                raise ValueError("Public key is not a hex string!")

        return key

    keys = {
        "public_key": public_key,
        "master_key": master_key
    }

    cleaned_keys = {
        name: clean_key(name, key)
        for name, key in keys.items()
    }

    if not cleaned_keys["master_key"] == MASTER_KEY:
        raise BadKeyException

    existing = await get_bike(public_key=cleaned_keys["public_key"])

    if existing is not None:
        return existing

    return await Bike.create(public_key_hex=cleaned_keys["public_key"].hex())


async def lock_bike(public_key, value) -> None:
    """
    Locks or unlocks the bike with a public key.

    :param public_key: The key for the bike.
    :param value: The locked or unlocked value.
    :return: True if successful.
    :raises ConnectionError: If the bike is not connected.
    """
    bike: Bike = await Bike.get(public_key_hex=public_key.hex()).first()
    try:
        await bike.set_locked(value)
    except ConnectionError as e:
        raise e


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
        bid = bike.id
    elif isinstance(bike, int):
        bid = bike
    else:
        raise TypeError("Must be bike id or bike.")

    return await RentalUpdate.filter(bike__id=bid)


async def get_user(firebase_id) -> User:
    """

    :return: The user with the given firebase id.
    """
    return await User.filter(firebase_id=firebase_id).first()
