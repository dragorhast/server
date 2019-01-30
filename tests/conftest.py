import asyncio
import os

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient
from faker import Faker
from faker.providers import address, internet, misc
from tortoise import Tortoise
from tortoise.transactions import start_transaction
from shapely.geometry import Polygon

from server.middleware import validate_token_middleware
from server.models import Bike, User, Rental
from server.models.pickup_point import PickupPoint
from server.service import TicketStore
from server.service.bike_connection_manager import BikeConnectionManager
from server.service.rental_manager import RentalManager
from server.service.verify_token import DummyVerifier
from server.signals import register_signals
from server.views import register_views

pytest_plugins = 'aiohttp.pytest_plugin'

fake = Faker()
fake.add_provider(address)
fake.add_provider(internet)
fake.add_provider(misc)


@pytest.fixture
def random_user_factory(database):
    async def create_user(is_admin=False):
        return await User.create(firebase_id=fake.sha1(), first=fake.name(), email=fake.email(), is_admin=is_admin)
    return create_user


@pytest.fixture
def random_bike_factory(database):
    async def create_bike():
        return await Bike.create(public_key_hex=fake.sha1())
    return create_bike


@pytest.yield_fixture(scope='function')
async def database(loop):
    database_url = os.getenv("DATABASE_URL", "sqlite://:memory:")

    await Tortoise.init(
        db_url=database_url,
        modules={'models': ['server.models']})
    await Tortoise.generate_schemas()
    transaction = await start_transaction()

    yield

    await transaction.rollback()
    await Tortoise.close_connections()


@pytest.fixture
async def client(aiohttp_client, loop, database) -> TestClient:
    asyncio.get_event_loop().set_debug(True)
    app = web.Application(middlewares=[validate_token_middleware])

    app['rental_manager'] = RentalManager()
    app['bike_location_manager'] = BikeConnectionManager()
    app['token_verifier'] = DummyVerifier()

    register_signals(app, init_database=False)  # we get the database from a fixture
    register_views(app, "/api/v1")

    return await aiohttp_client(app)


@pytest.fixture
def ticket_store():
    return TicketStore()


@pytest.fixture(scope="function")
def rental_manager():
    return RentalManager()


@pytest.fixture
async def random_bike(random_bike_factory) -> Bike:
    """Creates a random bike in the database."""
    return await random_bike_factory()


@pytest.fixture
async def random_user(random_user_factory) -> User:
    """Creates a random user in the database."""
    return await random_user_factory()


@pytest.fixture()
async def random_admin(random_user_factory) -> User:
    return await random_user_factory(True)


@pytest.fixture
async def random_rental(rental_manager, random_bike, random_user) -> Rental:
    """Creates a random rental in the database."""
    rental, location = await rental_manager.create(random_user, random_bike)
    return rental


@pytest.fixture
async def random_pickup_point(database) -> PickupPoint:
    return await PickupPoint.create(name=fake.street_name(), area=Polygon([(1, 1), (1, -1), (-1, -1), (-1, 1)]))
