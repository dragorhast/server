import pytest

from server.models import Rental, RentalUpdate, User
from server.models.util import RentalUpdateType
from server.service import InactiveRentalError, ActiveRentalError
from server.service.rental_manager import RentalManager


async def test_rebuild_rentals(rental_manager: RentalManager, random_user, random_bike):
    """Assert that rebuilding the rental manager from the database has the expected result."""
    rental = await Rental.create(user=random_user, bike=random_bike)
    await RentalUpdate.create(rental=rental, type=RentalUpdateType.RENT)
    await rental_manager.rebuild()

    assert rental_manager.active_rental_ids[random_user.id] == rental.id


async def test_create_rental(rental_manager, random_user, random_bike):
    """Assert that creating a rental correctly creates an event."""
    await rental_manager.create(random_user, random_bike)
    assert await Rental.all().count() == 1
    assert await RentalUpdate.all().count() == 1
    assert (await RentalUpdate.first()).type == RentalUpdateType.RENT


async def test_create_rental_existing_rental(rental_manager, random_rental, random_bike):
    """Assert that creating a second rental for a user """
    user = await User.filter(id=random_rental.user_id).first()
    with pytest.raises(ActiveRentalError):
        await rental_manager.create(user, random_bike)


async def test_finish_rental(rental_manager, random_rental):
    """Assert that finishing a rental correctly creates an event and charges the customer."""
    await rental_manager.finish(random_rental, extra_cost=2.0)
    rental = await Rental.first().prefetch_related('updates')
    assert rental.price >= 2.0
    assert len(rental.updates) == 2


async def test_finish_inactive_rental(rental_manager, random_user, random_bike):
    """Assert that finishing an inactive rental raises an exception."""
    rental = Rental(user=random_user, bike=random_bike)
    with pytest.raises(InactiveRentalError):
        await rental_manager.finish(rental)


async def test_cancel_rental(rental_manager, random_rental):
    """Assert that cancelling a rental correctly creates a cancellation event."""
    await rental_manager.cancel(random_rental)
    rental = await Rental.first()
    assert rental.price is None


async def test_cancel_inactive_rental(rental_manager, random_user, random_bike):
    """Assert that cancelling an inactive rental raises an exception."""
    rental = Rental(user=random_user, bike=random_bike)
    with pytest.raises(InactiveRentalError):
        await rental_manager.cancel(rental)
