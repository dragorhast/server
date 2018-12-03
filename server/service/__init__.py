"""
The service layer for the system. Acts as the internal API.
Each interface (REST API, web-sockets) should use the
service layer to implement their logic.

The service layer implements the use cases for the system.
"""
from typing import Optional, Union, Iterable

from server.models import Bike, User
from server.models.rental import Rental
from server.store import Store

store = Store()


async def get_bikes():
    """Gets all the bikes from the system."""
    return await store.get_bikes()


async def get_bike(*, bike_id: Optional[int] = None,
                   public_key: Optional[bytes] = None):
    """Gets a bike from the system."""
    return await store.get_bike(bike_id=bike_id, public_key=public_key)


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


async def get_users():
    return await store.get_users()


async def get_rentals(bike: Union[int, Bike]) -> Iterable[Rental]:
    """
    Gets rentals for a given bike.

    :param bike: The bike or id to fetch.
    :return: An iterable of rentals.
    """
    if isinstance(bike, Bike):
        bid = bike.bid
    elif isinstance(bike, int):
        bid = bike
    else:
        raise TypeError("Must be bike id or bike.")

    return await store.get_rentals(bike_id=bid)


async def start_rental(bike, user) -> Rental:
    return await store.add_rental(bike.bid, user.uid)


async def get_user() -> User:
    return next((await store.get_users()))