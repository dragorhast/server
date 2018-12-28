from aiohttp.test_utils import TestClient

from server.models.bike import Bike
from server.models.util import BikeType
from server.serializer import BikeSchema, RentalSchema
from server.serializer.jsend import JSendStatus, JSendSchema
from server.service import MASTER_KEY
from server.views import BikeRegisterSchema, AuthorizedSchema
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
    response_data = response_schema.load(await resp.json())
    assert response_data["status"] == JSendStatus.SUCCESS


async def test_register_bike_bad_public_key(client: TestClient):
    """Assert that a bad public key causes a failed request."""
    request_schema = BikeRegisterSchema()

    request_json = request_schema.dump({
        "public_key": random_key(1),
        "type": BikeType.ROAD,
    })

    request_json["public_key"] = "bad_key"

    resp = await client.post('/api/v1/bikes', json=request_json)

    response_schema = JSendSchema()
    response_data = response_schema.load(await resp.json())
    assert response_data["status"] == JSendStatus.FAIL
    assert any(
        "bad_key is not a valid hex-encoded string" in error
        for error in response_data["data"]["public_key"]
    )
    assert resp.status == 400


async def test_register_bike_bad_master_key(client: TestClient):
    """Assert that a bad master key causes a failed request."""
    request_schema = BikeRegisterSchema()
    request_data = {
        "public_key": random_key(32),
        "master_key": random_key(1),
        "type": BikeType.ROAD,
    }

    request_json = request_schema.dump(request_data)

    resp = await client.post('/api/v1/bikes', json=request_json)

    response_schema = JSendSchema()
    response_data = response_schema.load(await resp.json())
    assert response_data["status"] == JSendStatus.FAIL
    assert resp.status == 400


async def test_register_bike_bad_schema(client: TestClient):
    """Assert that a bad schema is dealt with."""
    resp = await client.post('/api/v1/bikes', json={"bad_key": "bad_key"})
    response_schema = JSendSchema()
    response_data = response_schema.load(await resp.json())
    assert response_data["status"] == JSendStatus.FAIL
    assert resp.status == 400


async def test_get_bike(client: TestClient):
    """Assert that you can get the data of a single bike."""

    bike = await Bike.create(public_key_hex=random_key(32))

    resp = await client.get(f'/api/v1/bikes/{bike.id}')

    schema = JSendSchema.of(BikeSchema())
    data = schema.load(await resp.json())

    assert data["data"]["id"] == bike.id


async def test_get_bike_missing(client: TestClient):
    """Assert that getting a non-existent bike causes a failure."""

    response = await client.get(f'/api/v1/bikes/1')
    response_schema = JSendSchema()
    data = response_schema.load(await response.json())

    assert data["status"] == JSendStatus.FAIL
    assert "Invalid" in data["data"]["id"]


async def test_get_bike_rentals(client: TestClient):
    """Assert that you can get the rentals for a given bike."""

    await test_register_bike(client)

    response = await client.get(f'/api/v1/bikes/1/rentals')
    response_schema = JSendSchema.of(RentalSchema(many=True))
    data = response_schema.load(await response.json())

    assert data["status"] == JSendStatus.SUCCESS


async def test_create_bike_rental(client: TestClient):
    """Assert that you can create a rental.

    todo mock get_user
    todo mock key validation
    """


async def test_create_bike_rental_missing_user(client: TestClient):
    """Assert that creating a rental with a non existing user (but valid firebase key) gives a descriptive error.

    todo mock key validation
    """

    await test_register_bike(client)
    request_schema = AuthorizedSchema()
    response_schema = JSendSchema()
    request_data = request_schema.load({
        "firebase_id": "mock"
    })

    response = await client.post(f'/api/v1/bikes/1/rentals', json=request_data)
    response_data = response_schema.load(await response.json())

    assert response_data["status"] == JSendStatus.FAIL
    assert "No such user exists" in response_data["data"]["firebase_id"]


async def test_create_bike_rental_invalid_key(client: TestClient):
    """Assert that creating a rental with an invalid firebase key fails."""

    await test_register_bike(client)
    request_schema = AuthorizedSchema()
    response_schema = JSendSchema()
    request_data = request_schema.load({
        "firebase_id": "mock"
    })

    response = await client.post(f'/api/v1/bikes/1/rentals', json=request_data)
    response_data = response_schema.load(await response.json())
