from aiohttp.test_utils import TestClient

from server.serializer import RentalSchema, JSendSchema, JSendStatus


class TestRentalsView:

    async def test_get_rentals(self, client: TestClient, random_user, random_bike):
        """Assert that you can get a list of all rentals."""
        await client.app["rental_manager"].create(random_user, random_bike)

        response = await client.get('/api/v1/rentals')
        response_schema = JSendSchema.of(RentalSchema(many=True))
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert len(response_data["data"]) == 1


class TestRentalView:

    async def test_get_rental(self, client: TestClient, random_user, random_bike):
        """Assert that you get get a single rental from the system."""
        rental = await client.app["rental_manager"].create(random_user, random_bike)

        response = await client.get(f'/api/v1/rentals/{rental.id}')
        response_schema = JSendSchema.of(RentalSchema())
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert response_data["data"]["id"] == rental.id
