import pytest

from server.models import Bike, BikeStateUpdate
from server.models.util import BikeUpdateType
from server.service import MASTER_KEY
from server.service.access.bikes import get_bikes, get_bike, register_bike, BadKeyError, delete_bike, \
    get_bike_in_circulation, set_bike_in_circulation
from tests.util import random_key


async def test_get_bikes(random_bike):
    """Assert that getting bikes returns all bikes."""
    bikes = await get_bikes()
    assert len(bikes) == 1
    assert bikes[0] == random_bike


async def test_get_bike(random_bike: Bike):
    """Assert that getting a bike returns it."""
    bike = await get_bike(public_key=random_bike.public_key)
    assert bike.id == random_bike.id
    bike = await get_bike(identifier=random_bike.identifier)
    assert bike.id == random_bike.id


async def test_get_bad_bike(database):
    """Assert that getting a bad bike returns None"""
    bike = await get_bike(identifier=-1)
    assert bike is None


async def test_create_bike(database):
    """Assert you can create a new bike with the master key."""
    bike = await register_bike(public_key=random_key(32), master_key=MASTER_KEY)
    assert bike


async def test_create_bike_bad_master(database):
    """Assert that creating a bike with the wrong key fails."""
    with pytest.raises(BadKeyError):
        await register_bike(random_key(32), "BADBAD")


@pytest.mark.parametrize("first_key", [0, 0.0, None, False])
@pytest.mark.parametrize("second_key", [0, 0.0, None, False])
async def test_create_bike_bad_type(database, first_key, second_key):
    """Assert that creating a bike with bad key types fails."""
    with pytest.raises(TypeError):
        await register_bike(first_key, second_key)


@pytest.mark.parametrize("key_name", ["key", "abc"])
async def test_create_bike_bad_value(database, key_name):
    """Assert that create a bike with an invalid hex fails."""
    with pytest.raises(ValueError):
        await register_bike(public_key=key_name, master_key=key_name)


async def test_create_bike_get_same(random_bike: Bike):
    """Assert that creating a new bike with an existing public key just returns the existing bike."""
    bike = await register_bike(public_key=random_bike.public_key, master_key=MASTER_KEY)
    assert bike == random_bike


async def test_create_bike_same_short_key(random_bike: Bike):
    with pytest.raises(BadKeyError):
        await register_bike(public_key=random_bike.public_key[:30] + bytes.fromhex("abcd"), master_key=MASTER_KEY)


async def test_delete_bike(random_bike):
    await delete_bike(random_bike, MASTER_KEY)
    assert await Bike.all().count() == 0


async def test_delete_bike_bad_master(random_bike):
    with pytest.raises(BadKeyError):
        await delete_bike(random_bike, "")


async def test_get_bike_status(random_bike):
    await BikeStateUpdate.create(bike=random_bike, state=BikeUpdateType.IN_CIRCULATION)
    status = await get_bike_in_circulation(random_bike)
    assert status is True


async def test_get_bike_status_no_status(random_bike):
    status = await get_bike_in_circulation(random_bike)
    assert status is False


async def test_set_bike_status(random_bike):
    await set_bike_in_circulation(random_bike, True)
    bike = await Bike.all().first().prefetch_related("state_updates")
    assert bike.in_circulation is True
