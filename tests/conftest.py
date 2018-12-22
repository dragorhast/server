import asyncio
import weakref

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient
from tortoise import Tortoise
from tortoise.transactions import start_transaction

from server.models import Bike
from server.signals import register_signals
from server.ticket_store import TicketStore
from server.views import register_views
from tests.util import random_key


@pytest.yield_fixture
async def database():
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={'models': ['server.models']})
    await Tortoise.generate_schemas()
    transaction = await start_transaction()

    yield

    await transaction.rollback()
    await Tortoise.close_connections()


@pytest.fixture
def client(aiohttp_client, loop) -> TestClient:
    asyncio.get_event_loop().set_debug(True)
    app = web.Application()

    app['bike_connections'] = weakref.WeakSet()
    app['database_uri'] = 'sqlite://:memory:'
    register_signals(app)
    register_views(app.router, "/api/v1")

    return loop.run_until_complete(aiohttp_client(app))


@pytest.fixture
def ticket_store():
    return TicketStore()


@pytest.fixture
async def random_bike(database) -> Bike:
    """Creates a random bike in the database."""
    return await Bike.create(public_key_hex=random_key(32))
