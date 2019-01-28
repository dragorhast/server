from aiohttp.test_utils import TestClient

from server.serializer import RentalSchema, JSendSchema, JSendStatus
from server.serializer.fields import Many


class TestRentalsView:

    async def test_get_rentals(self, client: TestClient, random_admin, random_bike):
        """Assert that you can get a list of all rentals."""
        await client.app["rental_manager"].create(random_admin, random_bike)

        response = await client.get('/api/v1/rentals', headers={"Authorization": f"Bearer {random_admin.firebase_id}"})
        response_schema = JSendSchema.of(rentals=Many(RentalSchema()))
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert len(response_data["data"]["rentals"]) == 1


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
