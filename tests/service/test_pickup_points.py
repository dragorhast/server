from server.service.pickup_point import get_pickup_points


async def test_get_pickup_points(random_pickup_point):
    points = await get_pickup_points()
    assert random_pickup_point in points
