from datetime import timedelta, datetime, timezone

from aiohttp.test_utils import TestClient
from marshmallow.fields import Dict, Nested, List

from server.models import Issue
from server.models.bike import Bike
from server.models.util import BikeType
from server.serializer.fields import Many, BytesField
from server.serializer.jsend import JSendStatus, JSendSchema
from server.serializer.models import CurrentRentalSchema, IssueSchema, BikeSchema, RentalSchema
from server.service import MASTER_KEY
from server.service.access.issues import open_issue
from server.serializer.misc import MasterKeySchema, BikeRegisterSchema
from tests.util import random_key


class TestBikesView:

    async def test_get_bikes(self, client: TestClient, random_bike):
        """Assert that anyone can get the entire list of bikes."""
        resp = await client.get('/api/v1/bikes')

        schema = JSendSchema.of(bikes=Many(BikeSchema()))
        data = schema.load(await resp.json())

        assert data["status"] == JSendStatus.SUCCESS
        assert isinstance(data["data"]["bikes"], list)
        assert len(data["data"]["bikes"]) == 1
        assert data["data"]["bikes"][0]["identifier"] == random_bike.identifier

    async def test_register_bike(self, client: TestClient):
        """Assert that a bike can register itself with the system."""
        request_schema = BikeRegisterSchema()
        request_data = {
            "public_key": random_key(32),
            "master_key": MASTER_KEY,
            "type": BikeType.ROAD,
        }

        request_json = request_schema.dump(request_data)

        response = await client.post('/api/v1/bikes', json=request_json)
        response_schema = JSendSchema.of(bike=BikeSchema())

        response_data = response_schema.load(await response.json())
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
            for error in response_data["data"]["errors"]["public_key"]
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


class TestBrokenBikesView:

    async def test_get_broken_bikes(self, client: TestClient, random_admin, random_bike):
        """Assert that an admin can get broken bikes from the system."""
        await open_issue(random_admin, "This is broken", random_bike)

        response = await client.get(f"/api/v1/bikes/broken",
                                    headers={"Authorization": f"Bearer {random_admin.firebase_id}"})

        response_data = JSendSchema.of(bikes=Many(BikeSchema())).load(await response.json())

        assert response_data["status"] == JSendStatus.SUCCESS
        assert len(response_data["data"]["bikes"]) == 1


class TestLowBikesView:

    async def test_get_low_bikes(self, client, random_bike_factory, random_admin, bike_connection_manager):
        """Assert that the system can retrieve all bikes with less than 30% battery."""
        bike_connection_manager.is_connected = lambda x: True
        bike_connection_manager.is_locked = lambda x: True
        bike_connection_manager.most_recent_location = lambda x: None

        bike1 = await random_bike_factory()
        bike2 = await random_bike_factory()

        bike_connection_manager.update_battery(bike1.id, 10)
        bike_connection_manager.update_battery(bike2.id, 40)

        response = await client.get("/api/v1/bikes/low", headers={"Authoization": f"Bearer {random_admin.firebase_id}"})
        response_data = JSendSchema().load(await response.json())
        assert len(response_data["data"]["bikes"]) == 1
        assert response_data["status"] == JSendStatus.SUCCESS


class TestBikeView:

    async def test_get_bike(self, client: TestClient, random_bike):
        """Assert that you can get the data of a single bike."""

        resp = await client.get(f'/api/v1/bikes/{random_bike.identifier}')

        schema = JSendSchema.of(bike=BikeSchema())
        data = schema.load(await resp.json())

        assert data["data"]["bike"]["identifier"] == random_bike.identifier

    async def test_get_bike_missing(self, client: TestClient):
        """Assert that getting a non-existent bike causes a failure."""

        response = await client.get(f'/api/v1/bikes/ababab')
        response_schema = JSendSchema()
        data = response_schema.load(await response.json())

        assert data["status"] == JSendStatus.FAIL
        assert "Could not find" in data["data"]["message"]

    async def test_delete_bike(self, client: TestClient, random_bike):
        """Assert that you can delete bikes with a valid master key."""

        request_schema = MasterKeySchema()
        request_data = request_schema.dump({
            "master_key": MASTER_KEY
        })

        response = await client.delete(f'/api/v1/bikes/{random_bike.identifier}', json=request_data)

        assert response.status == 204
        assert await Bike.filter(id=random_bike.id).first() is None

    async def test_delete_bike_bad_master(self, client: TestClient, random_bike):
        """Assert that passing the wrong key fails."""

        request_schema = MasterKeySchema()
        response_schema = JSendSchema()

        request_data = request_schema.dump({
            "master_key": "abcd"
        })

        response = await client.delete(f'/api/v1/bikes/{random_bike.identifier}', json=request_data)
        response_data = response_schema.load(await response.json())

        assert response_data["status"] == JSendStatus.FAIL
        assert "master key is invalid" in response_data["data"]["message"]


class TestBikeRentalsView:

    async def test_get_bike_rentals(self, client: TestClient, random_bike, random_admin):
        """Assert that you can get the rentals for a given bike."""

        response = await client.get(f'/api/v1/bikes/{random_bike.identifier}/rentals',
                                    headers={"Authorization": f"Bearer {random_admin.firebase_id}"})
        response_schema = JSendSchema.of(rentals=Many(RentalSchema()))
        response_data = response_schema.load(await response.json())

        assert response_data["status"] == JSendStatus.SUCCESS
        assert isinstance(response_data["data"]["rentals"], list)

    async def test_create_bike_rental(self, client: TestClient, random_user, random_bike):
        """Assert that you can create a rental."""
        response = await client.post(
            f'/api/v1/bikes/{random_bike.identifier}/rentals',
            headers={"Authorization": f"Bearer {random_user.firebase_id}"}
        )

        response_data = JSendSchema.of(rental=CurrentRentalSchema()).load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert "price" not in response_data["data"]["rental"]
        assert response_data["data"]["rental"]["bike_identifier"] == random_bike.identifier
        assert response_data["data"]["rental"]["user_id"] == random_user.id

    async def test_create_bike_rental_from_reservation(self, client, random_user, random_bike, reservation_manager,
                                                       random_pickup_point, bike_connection_manager):
        """
        Assert that a user can initiate a rental from the same pickup point as their current reservation.
        """
        bike_connection_manager.is_connected = lambda x: True
        await bike_connection_manager.update_location(random_bike, random_pickup_point.area.centroid)
        reservation_manager.pickup_points.add(random_pickup_point)
        await reservation_manager.reserve(random_user, random_pickup_point, datetime.now(timezone.utc) + timedelta(minutes=10))

        assert len(reservation_manager.reservations[random_pickup_point.id]) == 1

        response = await client.post(f"/api/v1/bikes/{random_bike.identifier}/rentals",
                                     headers={"Authorization": f"Bearer {random_user.firebase_id}"})

        response_data = JSendSchema().load(await response.json())

        assert len(reservation_manager.reservations[random_pickup_point.id]) == 0

    async def test_create_bike_rental_missing_user(self, client: TestClient, random_bike):
        """Assert that creating a rental with a non existing user (but valid firebase key) gives a descriptive error."""
        response = await client.post(f'/api/v1/bikes/{random_bike.identifier}/rentals',
                                     headers={"Authorization": "Bearer ab"})

        response_schema = JSendSchema()
        response_data = response_schema.load(await response.json())

        assert response_data["status"] == JSendStatus.FAIL
        assert "Could not find" in response_data["data"]["message"]

    async def test_create_bike_rental_bike_in_use(self, client, random_user, random_bike):
        """Assert that trying to create a bike rental with one already active fails."""
        await client.app["rental_manager"].create(random_user, random_bike)
        response = await client.post(
            f'/api/v1/bikes/{random_bike.identifier}/rentals',
            headers={"Authorization": f"Bearer {random_user.firebase_id}"}
        )

        response_data = JSendSchema().load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert "bike is in use" in response_data["data"]["message"]

    async def test_create_bike_rental_user_has_rental(self, client, random_user, random_bike_factory):
        """Assert that creating a bike rental with one active """
        bike_1 = await random_bike_factory()
        bike_2 = await random_bike_factory()

        await client.app["rental_manager"].create(random_user, bike_1)
        response = await client.post(f"/api/v1/bikes/{bike_2.identifier}/rentals",
                                     headers={"Authorization": f"Bearer {random_user.firebase_id}"})
        response_data = JSendSchema().load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert "already have an active" in response_data["data"]["message"]

    async def test_create_bike_rental_invalid_key(self, client: TestClient, random_bike):
        """Assert that creating a rental with an invalid firebase key fails."""
        response_schema = JSendSchema()
        response = await client.post(f'/api/v1/bikes/{random_bike.identifier}/rentals',
                                     headers={"Authorization": "Bearer invalid"})
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert any("Not a valid hex string." == error for error in response_data["data"]["errors"])


class TestBikeIssuesView:

    async def test_get_issues_for_bike(self, client, random_admin, random_bike):
        await Issue.create(user=random_admin, bike=random_bike, description="OMG AWFUL")
        response = await client.get(f"/api/v1/bikes/{random_bike.identifier}/issues", headers={"Authorization": f"Bearer {random_admin.firebase_id}"})
        response_data = JSendSchema.of(issues=Many(IssueSchema())).load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert "issues" in response_data["data"]
        assert all(issue["bike_identifier"] == random_bike.identifier for issue in response_data["data"]["issues"])

    async def test_create_issue_for_bike(self, client, random_user, random_bike):
        response = await client.post(
            f"/api/v1/bikes/{random_bike.identifier}/issues",
            headers={"Authorization": f"Bearer {random_user.firebase_id}"},
            json={"description": "I HATE IT"}
        )

        response_data = JSendSchema.of(issue=IssueSchema()).load(await response.json())
        assert response_data["data"]["issue"]["bike_identifier"] == random_bike.identifier
