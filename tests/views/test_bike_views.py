from aiohttp import ContentTypeError
from aiohttp.test_utils import TestClient

from server.models.bike import BikeType, Bike
from server.serializer import BikeSchema
from server.serializer.jsend import JSendStatus, JSendSchema
from server.service import MASTER_KEY
from server.views import BikeRegisterSchema
from tests.util import random_key


async def test_get_bikes(client: TestClient):
    """Assert that anyone can get the entire list of bikes."""
    resp = await client.get('/api/v1/bikes')

    schema = JSendSchema.of(BikeSchema(many=True))
    data = schema.load(await resp.json())

    assert data["status"] == JSendStatus.SUCCESS
    assert isinstance(data["data"], list)


async def test_register_bike(client: TestClient):
    """Assert that a bike can register itself with the system."""
    request_schema = BikeRegisterSchema()
    request_data = {
        "public_key": random_key(32),
        "master_key": MASTER_KEY,
        "type": BikeType.ROAD,
    }

    request_json = request_schema.dump(request_data)

    resp = await client.post('/api/v1/bikes', json=request_json)

    response_schema = JSendSchema.of(BikeSchema())
    try:
        response_data = response_schema.load(await resp.json())
    except ContentTypeError as e:
        print(await resp.text())
        raise e
    assert response_data["status"] == JSendStatus.SUCCESS


async def test_get_bike(client: TestClient):
    """Assert that you can get the data of a single bike."""

    bike = await Bike.create(public_key_hex=random_key(32))

    resp = await client.get(f'/api/v1/bikes/{bike.id}')

    schema = JSendSchema.of(BikeSchema())
    data = schema.load(await resp.json())

    assert data["data"]["id"] == bike.id


async def test_get_bike_missing(client: TestClient):
    """Assert that getting a non-existent bike causes a failure."""

    resp = await client.get(f'/api/v1/bikes/1')
    schema = JSendSchema()
    data = schema.load(await resp.json())

    assert data["status"] == JSendStatus.FAIL
