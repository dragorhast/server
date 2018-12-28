"""
This module is what handles all the rentals in the system.
"""

from collections import defaultdict
from typing import Dict, Set, Callable

from server.models import Bike, Rental, User, RentalUpdate
from server.models.util import RentalUpdateType
from server.pricing import get_price


class InactiveRentalError(Exception):
    pass


class ActiveRentalError(Exception):
    pass


class RentalManager:
    """
    Handles the lifecycle of the rental in the system.

    todo: When the server restarts with active rentals, they are not rebuilt.
    """

    def __init__(self):
        self._rentals = {}
        self._subscribers = defaultdict(set)

    _rentals: Dict[int, int]
    """Maps user ids to their current rental."""

    _subscribers: Dict[int, Set[Callable]]
    """Maps a rental to a set of event subscribers."""

    async def active_rentals(self):
        return await Rental.filter(id__in=self._rentals.keys())

    async def rebuild(self):
        """
        Rebuilds the currently active rentals from the database.

        todo Fix tortoise to correctly map types with the serializer
        """
        unfinished_rentals = await Rental.filter(
            updates__type__not_in=(t.value for t in RentalUpdateType.terminating_types()))
        for rental in unfinished_rentals:
            self._rentals[rental.user_id] = rental.id

    async def create(self, user: User, bike: Bike) -> Rental:
        """Creates a new rental for a user."""
        if user.id in self._rentals:
            raise ActiveRentalError

        rental = await Rental.create(user=user, bike=bike)
        await self._publish_event(rental, RentalUpdateType.RENT)
        self._rentals[user.id] = rental.id
        return rental

    async def finish(self, rental: Rental, *, extra_cost=0.0):
        """
        Completes a rental.

        :raises InactiveRentalError: When there is no active rental for that user.
        """
        user = await User.filter(id=rental.user_id).first()
        if user.id not in self._rentals:
            raise InactiveRentalError

        await self._publish_event(rental, RentalUpdateType.RETURN)
        rental_events = await RentalUpdate.filter(rental=rental).order_by('time')
        rental.price = await get_price(rental_events[0].time, rental_events[-1].time, extra_cost)
        del self._rentals[user.id]
        return await rental.save()

    async def cancel(self, rental: Rental):
        """Cancels a rental, effective immediately, waiving the rental fee."""
        user = await User.filter(id=rental.user_id).first()
        if user.id not in self._rentals:
            raise InactiveRentalError

        await self._publish_event(rental, RentalUpdateType.CANCEL)
        del self._rentals[user.id]
        return rental

    async def lock(self, rental: Rental, set_to: bool):
        """Locks a bike."""
        await self._publish_event(
            rental,
            RentalUpdateType.LOCK if set_to else RentalUpdateType.UNLOCK
        )

    async def _publish_event(self, rental: Rental, event_type: RentalUpdateType):
        await RentalUpdate.create(rental=rental, type=event_type)
        for subscriber in self._subscribers[rental]:
            subscriber(rental, event_type)

    def subscribe(self, rental: Rental, handler):
        """Subscribes a handler to a rental's events."""
        self._subscribers[rental].add(handler)

    def unsubscribe(self, rental: Rental, handler):
        """Un-subscribes a handler from a rental's events."""
        self._subscribers[rental].remove(handler)


rental_manager = RentalManager()
rental_manager.rebuild()
