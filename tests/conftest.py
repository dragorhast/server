import pytest
from tortoise import Tortoise
from tortoise.transactions import start_transaction

from server.models import Bike
from server.ticket_store import TicketStore
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
def ticket_store():
    return TicketStore()


@pytest.fixture
async def random_bike(database) -> Bike:
    """Creates a random bike in the database."""
    return await Bike.create(public_key_hex=random_key(32))
