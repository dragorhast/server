import asyncio
import weakref

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient
from tortoise import Tortoise
from tortoise.transactions import start_transaction

from server.models import Bike, User, Rental
from server.service import TicketStore
from server.service.rental_manager import RentalManager
from server.signals import register_signals
from server.views import register_views
from tests.util import random_key


@pytest.yield_fixture
async def database(loop):
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={'models': ['server.models']})
    await Tortoise.generate_schemas()
    transaction = await start_transaction()

    yield

    await transaction.rollback()
    await Tortoise.close_connections()


@pytest.fixture
async def client(aiohttp_client, loop) -> TestClient:
    asyncio.get_event_loop().set_debug(True)
    app = web.Application()

    app['bike_connections'] = weakref.WeakSet()
    app['database_uri'] = 'sqlite://:memory:'
    register_signals(app)
    register_views(app.router, "/api/v1")

    return await aiohttp_client(app)


@pytest.fixture
def ticket_store():
    return TicketStore()


@pytest.fixture(scope="function")
def rental_manager():
    return RentalManager()


@pytest.fixture
async def random_bike(database) -> Bike:
    """Creates a random bike in the database."""
    return await Bike.create(public_key_hex=random_key(32))


@pytest.fixture
async def random_user(database) -> User:
    """Creates a random user in the database."""
    return await User.create(firebase_id="test_user", first="Alex", email="test@test.com")


@pytest.fixture
async def random_rental(rental_manager, random_bike, random_user) -> Rental:
    """Creates a random rental in the database."""
    return await rental_manager.create(random_user, random_bike)
