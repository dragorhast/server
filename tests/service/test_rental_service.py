from server.service.rentals import get_rentals_for_bike, get_rental_with_distance


async def test_get_rentals_for_bike(random_bike, random_rental):
    rentals = await get_rentals_for_bike(random_bike)
    assert len(rentals) == 1


async def test_get_rental_with_distance(random_rental):
    rentals = await get_rental_with_distance(random_rental)
    pass

