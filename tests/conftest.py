import asyncio
import os
from datetime import datetime
from itertools import count

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient
from faker import Faker
from faker.providers import address, internet, misc
from shapely.geometry import Polygon, Point
from tortoise import Tortoise
from tortoise.exceptions import OperationalError
from tortoise.transactions import start_transaction

from server.middleware import validate_token_middleware
from server.models import Bike, User, Rental
from server.models.pickup_point import PickupPoint
from server.models.user import UserType
from server.service import TicketStore
from server.service.background.reservation_sourcer import ReservationSourcer
from server.service.background.stats_reporter import StatisticsReporter
from server.service.manager.bike_connection_manager import BikeConnectionManager
from server.service.manager.rental_manager import RentalManager
from server.service.manager.reservation_manager import ReservationManager
from server.service.payment import DummyPaymentManager
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
    user_id = count(1)

    async def create_user(is_admin=False):
        return await User.create(
            firebase_id=fake.sha1(), first=fake.name(), email=fake.email(),
            type=UserType.MANAGER if is_admin else UserType.USER, stripe_id="cus_" + hex(next(user_id))
        )

    return create_user


@pytest.fixture
def random_bike_factory(database):
    async def create_bike(bike_connection_manager):
        bike = await Bike.create(public_key_hex=fake.sha1())
        await bike_connection_manager.update_location(bike, Point(0, 0))
        await bike.fetch_related("location_updates")
        return bike

    return create_bike


@pytest.fixture(scope="session")
def database_url():
    return os.getenv("DATABASE_URL", "spatialite://:memory:")


async def init_db(database_url):
    try:
        await Tortoise.init(
            db_url=database_url,
            modules={'models': ['server.models']},
            _create_db=True
        )
    except OperationalError:
        # database already exists, drop it and rebuild
        await Tortoise.init(
            db_url=database_url,
            modules={'models': ['server.models']}
        )
        await Tortoise._drop_databases()
        await Tortoise.init(
            db_url=database_url,
            modules={'models': ['server.models']},
            _create_db=True
        )

    await Tortoise.generate_schemas(safe=True)
    await Tortoise.close_connections()


@pytest.fixture
def reservation_sourcer(reservation_manager):
    return ReservationSourcer(reservation_manager)


@pytest.fixture
def statistics_reporter(rental_manager, reservation_manager):
    return StatisticsReporter(rental_manager, reservation_manager)


@pytest.fixture(scope="session")
def _database(database_url):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(init_db(database_url))


@pytest.fixture
async def database(_database, loop, database_url):
    start = datetime.now()
    await Tortoise.init(
        db_url=database_url,
        modules={'models': ['server.models']},
    )

    if database_url.endswith(":memory:"):
        await Tortoise.generate_schemas(safe=True)

    init = datetime.now()
    transaction = await start_transaction()
    yield
    await transaction.rollback()
    await Tortoise.close_connections()

    print(f"Start: {start}")
    print(f"Init: {init} ({init - start})")


@pytest.fixture
async def client(
    aiohttp_client, database,
    rental_manager, payment_manager, bike_connection_manager, reservation_manager, reservation_sourcer, statistics_reporter
) -> TestClient:
    asyncio.get_event_loop().set_debug(True)
    app = web.Application(middlewares=[validate_token_middleware])

    app['payment_manager'] = payment_manager
    app['rental_manager'] = rental_manager
    app['bike_location_manager'] = bike_connection_manager
    app['reservation_manager'] = reservation_manager
    app['reservation_sourcer'] = reservation_sourcer
    app['statistics_reporter'] = statistics_reporter
    app['token_verifier'] = DummyVerifier()

    register_signals(app, init_database=False)  # we get the database from a fixture
    register_views(app, "/api/v1")

    return await aiohttp_client(app)


@pytest.fixture
def ticket_store():
    return TicketStore()


@pytest.fixture
def bike_connection_manager(database):
    return BikeConnectionManager()


@pytest.fixture
def payment_manager():
    return DummyPaymentManager()


@pytest.fixture
def rental_manager(database, payment_manager):
    return RentalManager(payment_manager)


@pytest.fixture
def reservation_manager(database, bike_connection_manager, rental_manager) -> ReservationManager:
    return ReservationManager(bike_connection_manager, rental_manager)


@pytest.fixture
async def random_bike(random_bike_factory, bike_connection_manager) -> Bike:
    """Creates a random bike in the database."""
    return await random_bike_factory(bike_connection_manager)


@pytest.fixture
async def random_user(random_user_factory) -> User:
    """Creates a random user in the database."""
    return await random_user_factory()


@pytest.fixture()
async def random_admin(random_user_factory) -> User:
    return await random_user_factory(True)


@pytest.fixture
async def random_rental(rental_manager, random_bike, random_user, bike_connection_manager) -> Rental:
    """Creates a random rental in the database."""
    await bike_connection_manager.update_location(random_bike, Point(0, 0))
    rental, location = await rental_manager.create(random_user, random_bike)
    rental.bike = random_bike
    return rental


@pytest.fixture
async def random_pickup_point(database) -> PickupPoint:
    return await PickupPoint.create(name=fake.street_name(), area=Polygon([(1, 1), (1, -1), (-1, -1), (-1, 1)]))
