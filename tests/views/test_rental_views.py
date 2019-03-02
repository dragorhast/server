from aiohttp.test_utils import TestClient

from server.serializer import JSendSchema, JSendStatus
from server.serializer.fields import Many
from server.serializer.models import RentalSchema


class TestRentalsView:

    async def test_get_rentals(self, client: TestClient, random_admin, random_bike):
        """Assert that you can get a list of all rentals."""
        await client.app["rental_manager"].create(random_admin, random_bike)

        response = await client.get('/api/v1/rentals', headers={"Authorization": f"Bearer {random_admin.firebase_id}"})
        response_schema = JSendSchema.of(rentals=Many(RentalSchema()))
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert len(response_data["data"]["rentals"]) == 1
        rental = response_data["data"]["rentals"][0]
        assert rental["bike_identifier"] == random_bike.identifier
        assert (await client.get(rental["bike_url"])).status != 404


class TestRentalView:

    async def test_get_rental(self, client: TestClient, random_admin, random_bike):
        """Assert that you get gets a single rental from the system."""
        rental, location = await client.app["rental_manager"].create(random_admin, random_bike)

        response = await client.get(f'/api/v1/rentals/{rental.id}',
                                    headers={"Authorization": f"Bearer {random_admin.firebase_id}"})
        response_schema = JSendSchema.of(rental=RentalSchema())
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert response_data["data"]["rental"]["id"] == rental.id
        assert response_data["data"]["rental"]["bike_identifier"] == random_bike.identifier
        assert (await client.get(response_data["data"]["rental"]["bike_url"])).status != 404
