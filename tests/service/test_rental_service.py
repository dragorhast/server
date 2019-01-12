from server.service.rentals import get_rentals_for_bike


async def test_get_rentals_for_bike(random_bike, random_rental):
    rentals = await get_rentals_for_bike(random_bike)
    assert len(rentals) == 1
