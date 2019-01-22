"""
Bikes
-----
"""
from datetime import datetime
from typing import Iterable, Optional, Dict, Union, Tuple

from shapely.geometry import Point
from shapely.wkt import loads
from tortoise.exceptions import DoesNotExist

from server.models import Bike
from server.models.location_update import LocationUpdate
from server.service import MASTER_KEY


class BikeLocationManager:
    """
    Maintains bike location state.
    """

    def __init__(self):
        self._bike_locations: Dict[int, Tuple[Point, datetime]] = {}

    def most_recent_location(self, target: Union[Bike, int]) -> Tuple[Point, datetime]:
        bid = target.id if isinstance(target, Bike) else target
        return self._bike_locations[bid]

    def update_location(self, target: Union[Bike, int], location: Point, time: Optional[datetime] = None):
        bid = target.id if isinstance(target, Bike) else target
        time = time if time is not None else datetime.now()
        LocationUpdate.create(bike=bid, location=location, time=time)
        self._bike_locations[bid] = (location, time)

    async def rebuild(self):
        """Rebuilds the bike location state from the database."""
        recent_updates = await LocationUpdate._meta.db.execute_query(
            "select U.bike_id, max(U.time) as 'time', ST_AsText(U.location) as 'location' from locationupdate U group by U.bike_id")
        for update in recent_updates:
            self._bike_locations[update["bike_id"]] = (
            loads(update["location"]), datetime.strptime(update["time"], "%Y-%m-%d %H:%M:%S"))


async def get_bikes() -> Iterable[Bike]:
    """Gets all the bikes from the system."""
    return await Bike.all()


async def get_bike(*, bike_id: Optional[int] = None,
                   public_key: Optional[bytes] = None,
                   public_key_short: Optional[bytes] = None) -> Optional[Bike]:
    """Gets a bike from the system."""
    kwargs: Dict = {}

    if bike_id:
        kwargs["id"] = bike_id
    if public_key:
        kwargs["public_key_hex"] = public_key.hex()
    if public_key_short:
        kwargs["public_key_hex__startswith"] = public_key_short.hex()

    try:
        return await Bike.get(**kwargs).first()
    except DoesNotExist:
        return None


async def register_bike(public_key: Union[str, bytes], master_key: Union[str, bytes]) -> Bike:
    """
    Register a bike with the system, and return it.

    :param public_key: The public key, or a string hex representation of it.
    :param master_key: The master key, or a string hex representation of it.
    :raises TypeError: if the key is not the right type
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
                raise ValueError("Public key is not a hex string!")

        return key

    public_key = clean_key("Public Key", public_key)
    master_key = clean_key("Master Key", master_key)

    if not master_key == MASTER_KEY:
        raise BadKeyError("Incorrect master key")

    existing = await get_bike(public_key_short=public_key[:3])

    if existing is not None:
        if existing.public_key != public_key:
            raise BadKeyError("Bike with that shortened key exists.")
        return existing

    return await Bike.create(public_key_hex=public_key.hex())


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
    except ConnectionError as error:
        raise error


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


class BadKeyError(Exception):
    pass
