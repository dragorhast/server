import pytest
from shapely.geometry import Point

from server.models import Rental, RentalUpdate, User, LocationUpdate
from server.models.util import RentalUpdateType
from server.service import InactiveRentalError, ActiveRentalError
from server.service.manager.rental_manager import RentalManager


async def test_rebuild_rentals(rental_manager: RentalManager, random_user, random_bike):
    """Assert that rebuilding the rental manager from the database has the expected result."""
    rental = await Rental.create(user=random_user, bike=random_bike)
    await RentalUpdate.create(rental=rental, type=RentalUpdateType.RENT)
    await rental_manager._rebuild()

    assert rental_manager._active_rentals[random_user.id] == (rental.id, random_bike.id)


async def test_create_rental(rental_manager, random_user, random_bike, bike_connection_manager):
    """Assert that creating a rental correctly creates an event."""
    await bike_connection_manager.update_location(random_bike, Point(0, 0))
    await rental_manager.create(random_user, random_bike)
    assert await Rental.all().count() == 1
    assert await RentalUpdate.all().count() == 1
    assert (await RentalUpdate.first()).type == RentalUpdateType.RENT


async def test_create_rental_existing_rental(rental_manager, random_rental, random_bike, bike_connection_manager):
    """Assert that creating a second rental for a user """
    user = await User.filter(id=random_rental.user_id).first()
    await bike_connection_manager.update_location(random_bike, Point(0, 0))
    with pytest.raises(ActiveRentalError):
        await rental_manager.create(user, random_bike)


async def test_finish_rental(rental_manager, random_rental, random_user):
    """Assert that finishing a rental correctly creates an event and charges the customer."""
    await rental_manager.finish(random_user, extra_cost=2.0)
    rental = await Rental.first().prefetch_related('updates')
    assert rental.price >= 2.0
    assert len(rental.updates) == 2


async def test_finish_inactive_rental(rental_manager, random_user, random_bike):
    """Assert that finishing an inactive rental raises an exception."""
    rental = Rental(user=random_user, bike=random_bike)
    with pytest.raises(InactiveRentalError):
        await rental_manager.finish(random_user)


async def test_cancel_rental(rental_manager, random_rental):
    """Assert that cancelling a rental correctly creates a cancellation event."""
    await rental_manager.cancel(random_rental.user)
    rental = await Rental.first()
    assert rental.price is None


async def test_cancel_inactive_rental(rental_manager, random_user):
    """Assert that cancelling an inactive rental raises an exception."""
    with pytest.raises(InactiveRentalError):
        await rental_manager.cancel(random_user)


async def test_user_has_active_rental(rental_manager, random_user, random_rental):
    """Assert that the rental manager correctly reports when a user has a rental."""
    assert rental_manager.has_active_rental(random_user)


async def test_active_rentals(rental_manager, random_rental):
    """Assert that you can retrieve the active rentals."""
    rentals = await rental_manager.active_rentals()
    assert rentals
    assert random_rental in rentals


async def test_active_rental(rental_manager, random_rental, random_user):
    """Assert that you can get a rental for a given user."""
    rental = await rental_manager.active_rental(random_user)
    assert rental == random_rental


async def test_active_rental_with_locations(rental_manager, random_rental, random_user, random_bike):
    """Assert that you can get a rental for a given user with locations."""
    update = await LocationUpdate.create(bike=random_bike, location=Point(0, 0))
    rental, start, current = await rental_manager.active_rental(random_user, with_locations=True)
    assert rental == random_rental
    assert start == update.location
    assert current == update.location


async def test_bike_is_in_use(rental_manager, random_rental, random_bike, random_bike_factory, bike_connection_manager):
    """Assert that you can check if a bike is in use."""
    assert rental_manager.is_in_use(random_bike)
    assert not rental_manager.is_in_use(await random_bike_factory(bike_connection_manager))


async def test_is_renting(rental_manager, random_rental, random_bike, random_user):
    """Assert that you can check if a user is renting a given bike."""
    assert rental_manager.is_renting(random_user.id, random_bike.id)
