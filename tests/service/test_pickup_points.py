from server.service.access.pickup_points import get_pickup_points, get_pickup_at


class TestPickups:

    async def test_get_pickups(self, random_pickup_point):
        points = await get_pickup_points()
        assert random_pickup_point in points

    async def test_get_pickups_by_name(self, random_pickup_point):
        pass

    async def test_get_pickups_at_location(self, random_pickup_point):
        location = random_pickup_point.area.centroid
        pickup = await get_pickup_at(location)
        assert random_pickup_point == pickup

    async def test_get_pickups_near(self):
        """Assert that you can get pickup points near a location from the server."""
        # await get_pickups_near(location, distance=10)
