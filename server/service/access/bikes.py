"""
Bikes
-----

Handles the CRUD for aw bike.

Bike registration is protected with a pass code such that new bikes may not
be registered without it. The password is (for now) a simple hex string but,
upon actual deployment, will be replaced with a more secure method.
"""
from typing import Optional, Dict, Union, List

from tortoise.exceptions import DoesNotExist
from tortoise.query_utils import Prefetch

from server.models import Bike, LocationUpdate
from server.service import MASTER_KEY


class BadKeyError(Exception):
    pass


async def get_bikes() -> List[Bike]:
    """Gets all the bikes from the system."""
    bikes = await Bike.all().prefetch_related(Prefetch("updates", queryset=LocationUpdate.all().limit(100)))
    return bikes


async def get_bike(*, identifier: Union[str, bytes] = None,
                   public_key: bytes = None) -> Optional[Bike]:
    """Gets a bike from the system."""
    kwargs: Dict = {}

    if public_key:
        kwargs["public_key_hex"] = public_key.hex()
    if identifier:
        kwargs["public_key_hex__startswith"] = identifier.hex() if isinstance(identifier, bytes) else identifier

    try:
        return await Bike.get(**kwargs).first().prefetch_related(Prefetch("updates", queryset=LocationUpdate.all().limit(100)))
    except DoesNotExist:
        return None


async def register_bike(public_key: Union[str, bytes], master_key: Union[str, bytes]) -> Bike:
    """
    Register a bike with the system, and return it.

    :param public_key: The public key, or a string hex representation of it.
    :param master_key: The master key, or a string hex representation of it.
    :raises TypeError: If the key is not the right type
    :raises ValueError: If the key is not hex string
    :raises BadKeyError: If the master key is not correct
    """

    def clean_key(name, key) -> bytes:
        if not isinstance(key, str) and not isinstance(key, bytes):
            raise TypeError(f"{name} has incorrect type {type(key)}")

        if isinstance(key, str):
            try:
                return bytes.fromhex(key)
            except ValueError:
                raise ValueError(f"{name} key is not a hex string!")

        return key

    public_key = clean_key("Public Key", public_key)
    master_key = clean_key("Master Key", master_key)

    if not master_key == MASTER_KEY:
        raise BadKeyError("Incorrect master key")

    existing = await get_bike(identifier=public_key[:3])

    if existing is not None:
        if existing.public_key != public_key:
            raise BadKeyError("Bike with that shortened key exists.")
        return existing

    return await Bike.create(public_key_hex=public_key.hex())


async def delete_bike(bike, master_key) -> None:
    """
    Deletes a bike.

    :param bike:
    :param master_key:
    :raises BadKeyError: If the master key is invalid.
    """
    if not master_key == MASTER_KEY:
        raise BadKeyError("Incorrect master key")

    await bike.delete()
