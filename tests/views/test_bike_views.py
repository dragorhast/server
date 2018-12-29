from aiohttp.test_utils import TestClient

from server.models.bike import Bike
from server.models.util import BikeType
from server.serializer import BikeSchema, RentalSchema
from server.serializer.jsend import JSendStatus, JSendSchema
from server.service import MASTER_KEY
from server.views.bikes import BikeRegisterSchema, AuthorizedSchema, MasterKeySchema
from tests.util import random_key


class TestBikesView:

    async def test_get_bikes(self, client: TestClient):
        """Assert that anyone can get the entire list of bikes."""
        resp = await client.get('/api/v1/bikes')

        schema = JSendSchema.of(BikeSchema(many=True))
        data = schema.load(await resp.json())

        assert data["status"] == JSendStatus.SUCCESS
        assert isinstance(data["data"], list)

    async def test_register_bike(self, client: TestClient):
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

    async def test_register_bike_bad_public_key(self, client: TestClient):
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

    async def test_register_bike_bad_master_key(self, client: TestClient):
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

    async def test_register_bike_bad_schema(self, client: TestClient):
        """Assert that a bad schema is dealt with."""
        resp = await client.post('/api/v1/bikes', json={"bad_key": "bad_key"})
        response_schema = JSendSchema()
        response_data = response_schema.load(await resp.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert resp.status == 400


class TestBikeView:

    async def test_get_bike(self, client: TestClient, random_bike):
        """Assert that you can get the data of a single bike."""

        resp = await client.get(f'/api/v1/bikes/{random_bike.id}')

        schema = JSendSchema.of(BikeSchema())
        data = schema.load(await resp.json())

        assert data["data"]["id"] == random_bike.id

    async def test_get_bike_missing(self, client: TestClient):
        """Assert that getting a non-existent bike causes a failure."""

        response = await client.get(f'/api/v1/bikes/1')
        response_schema = JSendSchema()
        data = response_schema.load(await response.json())

        assert data["status"] == JSendStatus.FAIL
        assert "Invalid" in data["data"]["id"]

    async def test_delete_bike(self, client: TestClient, random_bike):
        """Assert that you can delete bikes with a valid master key."""

        request_schema = MasterKeySchema()
        request_data = request_schema.dump({
            "master_key": MASTER_KEY
        })

        response = await client.delete(f'/api/v1/bikes/{random_bike.id}', json=request_data)

        assert response.status == 204
        assert await Bike.filter(id=random_bike.id).first() is None

    async def test_delete_bike_bad_master(self, client: TestClient, random_bike):
        """Assert that passing the wrong key fails."""

        request_schema = MasterKeySchema()
        response_schema = JSendSchema()

        request_data = request_schema.dump({
            "master_key": "abcd"
        })

        response = await client.delete(f'/api/v1/bikes/{random_bike.id}', json=request_data)
        response_data = response_schema.load(await response.json())

        assert response_data["status"] == JSendStatus.FAIL
        assert any("Incorrect master key" in error for error in response_data["data"])


class TestBikeRentalsView:

    async def test_get_bike_rentals(self, client: TestClient, random_bike):
        """Assert that you can get the rentals for a given bike."""

        response = await client.get(f'/api/v1/bikes/1/rentals')
        response_schema = JSendSchema.of(RentalSchema(many=True))
        data = response_schema.load(await response.json())

        assert data["status"] == JSendStatus.SUCCESS

    async def test_create_bike_rental(self, client: TestClient, random_user, random_bike):
        """Assert that you can create a rental."""

    async def test_create_bike_rental_missing_user(self, client: TestClient, random_bike):
        """Assert that creating a rental with a non existing user (but valid firebase key) gives a descriptive error.
        """

        request_schema = AuthorizedSchema()
        response_schema = JSendSchema()
        request_data = request_schema.load({
            "firebase_id": "mock"
        })

        response = await client.post(f'/api/v1/bikes/1/rentals', json=request_data)
        response_data = response_schema.load(await response.json())

        assert response_data["status"] == JSendStatus.FAIL
        assert "No such user exists" in response_data["data"]["firebase_id"]

    async def test_create_bike_rental_invalid_key(self, client: TestClient, random_bike):
        """Assert that creating a rental with an invalid firebase key fails."""

        response_schema = JSendSchema()

        client: TestClient = client

        response = await client.post(f'/api/v1/bikes/{random_bike.id}/rentals', headers={"Authorization": "Bearer invalid"})
        text = await response.text()
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert response_data["data"]["token"] == "Not a valid hex string."
