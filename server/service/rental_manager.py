"""
Rental Manager
--------------

This module is what handles all the rentals in the system.
"""

from collections import defaultdict
from datetime import datetime
from typing import Dict, Set, Callable, Union, Tuple

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
    """

    def __init__(self):
        self.active_rental_ids: Dict[int, int] = {}
        """Maps user ids to their current rental."""

        self._subscribers: Dict[int, Set[Callable]] = defaultdict(set)
        """Maps a rental to a set of event subscribers."""

    async def active_rentals(self):
        return await Rental.filter(id__in=self.active_rental_ids.keys()).prefetch_related('updates')

    async def active_rental(self, user: Union[int, User]):
        if isinstance(user, int):
            user_id = user
        if isinstance(user, User):
            user_id = user.id

        rental_id = self.active_rental_ids[user_id]
        return await Rental.filter(id=rental_id).first().prefetch_related('updates')

    async def get_price_estimate(self, target: Union[Rental, int]):
        """Gets the price of the rental so far."""

        if isinstance(target, int):
            rental = await Rental.filter(id=target).first()
        elif isinstance(target, Rental):
            rental = target

        return await get_price(rental.start_date, datetime.now())

    async def bike_in_use(self, target: Union[Bike, int]):
        """Checks whether the given bike is in use."""
        if isinstance(target, int):
            bike_id = target
        elif isinstance(target, Bike):
            bike_id = target.id

        return await Rental.filter(id__in=self.active_rental_ids.keys(), bike_id=bike_id).count() == 1

    async def rebuild(self):
        """
        Rebuilds the currently active rentals from the database.
        """
        unfinished_rentals = await Rental.filter(
            updates__type__not_in=(t.value for t in RentalUpdateType.terminating_types()))
        for rental in unfinished_rentals:
            self.active_rental_ids[rental.user_id] = rental.id

    async def create(self, user: User, bike: Bike) -> Rental:
        """Creates a new rental for a user."""
        if user.id in self.active_rental_ids:
            raise ActiveRentalError

        rental = await Rental.create(user=user, bike=bike)

        await self._publish_event(rental, RentalUpdateType.RENT)
        self.active_rental_ids[user.id] = rental.id

        return rental

    async def _resolve_target(self, target: Union[Rental, User]) -> Tuple[Rental, User]:
        """Given a rental or user, "resolves" the rental, user pair."""
        if isinstance(target, Rental):
            rental = target
            user = await User.filter(id=rental.user_id).first()
            if user.id not in self.active_rental_ids or not self.active_rental_ids[user.id] == rental.id:
                raise InactiveRentalError("Given rental is not the active rental for the user!")
        elif isinstance(target, User):
            user = target
            if user.id not in self.active_rental_ids:
                raise InactiveRentalError("Given user has no active rentals!")
            rental = await Rental.filter(id=self.active_rental_ids[target.id]).first()
        else:
            raise TypeError(f"Supplied target must be a Rental or User, not {type(target)}")

        return rental, user

    async def finish(self, target: Union[Rental, User], *, extra_cost=0.0):
        """
        Completes a rental.

        :raises InactiveRentalError: When there is no active rental for that user, or the given rental is not active.
        """
        rental, user = await self._resolve_target(target)

        await self._publish_event(rental, RentalUpdateType.RETURN)
        rental_events = await RentalUpdate.filter(rental=rental).order_by('time')
        rental.price = await get_price(rental_events[0].time, rental_events[-1].time, extra_cost)
        del self.active_rental_ids[user.id]
        return await rental.save()

    async def cancel(self, rental: Rental):
        """Cancels a rental, effective immediately, waiving the rental fee."""
        user = await User.filter(id=rental.user_id).first()
        if user.id not in self.active_rental_ids:
            raise InactiveRentalError

        await self._publish_event(rental, RentalUpdateType.CANCEL)
        del self.active_rental_ids[user.id]
        return rental

    async def lock(self, rental: Rental, set_to: bool):
        """Locks a bike."""
        await self._publish_event(
            rental,
            RentalUpdateType.LOCK if set_to else RentalUpdateType.UNLOCK
        )

    async def _publish_event(self, rental: Rental, event_type: RentalUpdateType):
        update = await RentalUpdate.create(rental=rental, type=event_type)

        if rental.updates._fetched:
            rental.updates.related_objects.append(update)

        for subscriber in self._subscribers[rental]:
            subscriber(rental, event_type)

    def subscribe(self, rental: Rental, handler):
        """Subscribes a handler to a rental's events."""
        self._subscribers[rental].add(handler)

    def unsubscribe(self, rental: Rental, handler):
        """Un-subscribes a handler from a rental's events."""
        self._subscribers[rental].remove(handler)
