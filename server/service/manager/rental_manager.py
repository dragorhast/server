"""
Rental Manager
--------------

This module is what handles all the rentals in the system.

Responsibilities
================

This object handles everything needed for bike rentals.

- creating a rental
- checking rental availability
- getting active rentals
- estimating rental price
"""

from collections import defaultdict
from datetime import datetime
from typing import Dict, Set, Callable, Union, Tuple, List

from shapely.geometry import Point
from tortoise.query_utils import Prefetch

from server.models import Bike, Rental, User, RentalUpdate, LocationUpdate
from server.models.util import RentalUpdateType
from server.pricing import get_price
from server.service.access.rentals import get_rental


class InactiveRentalError(Exception):
    pass


class ActiveRentalError(Exception):
    """Raised when an user tries to do an operation that requires no active rental."""

    def __init__(self, rental_id):
        self.rental_id = rental_id


class CurrentlyRentedError(Exception):

    def __init__(self, message, available_bikes):
        self.message = message
        self.available_bikes = available_bikes


class RentalManager:
    """Handles the lifecycle of the rental in the system."""

    def __init__(self):
        self._active_rentals: Dict[int, Tuple[int, int]] = {}
        """Maps user ids to a tuple containing their current rental and current bike."""

        self._subscribers: Dict[int, Set[Callable]] = defaultdict(set)
        """Maps a rental to a set of event subscribers."""

    async def create(self, user: User, bike: Bike) -> Tuple[Rental, Point]:
        """
        Creates a new rental for a user.

        :raises ActiveRentalError: If the requested user currently has a rental active.
        :raises CurrentlyRentedError: If the requested bike is currently in use.
        """
        if user.id in self._active_rentals:
            raise ActiveRentalError(self._active_rentals[user.id])

        if self.is_in_use(bike):
            raise CurrentlyRentedError("The requested bike is in use.", [])

        rental = await Rental.create(user=user, bike=bike)
        rental.bike = bike
        rental.user = user

        await self._publish_event(rental, RentalUpdateType.RENT)
        self._active_rentals[user.id] = (rental.id, bike.id)
        current_location = await LocationUpdate.filter(bike=bike).first()

        return rental, current_location.location if current_location is not None else None

    async def finish(self, target: Union[Rental, User], *, extra_cost=0.0) -> Rental:
        """
        Completes a rental.

        :raises InactiveRentalError: When there is no active rental for that user, or the given rental is not active.
        """
        rental, user = await self._resolve_target(target)

        await self._publish_event(rental, RentalUpdateType.RETURN)
        rental_events = await RentalUpdate.filter(rental=rental).order_by('time')
        rental.price = await get_price(rental_events[0].time, rental_events[-1].time, extra_cost)
        del self._active_rentals[user.id]
        await rental.save()
        return rental

    async def cancel(self, target: Union[Rental, User]) -> Rental:
        """Cancels a rental, effective immediately, waiving the rental fee."""
        rental, user = await self._resolve_target(target)

        await self._publish_event(rental, RentalUpdateType.CANCEL)
        del self._active_rentals[user.id]
        return rental

    async def active_rentals(self) -> List[Rental]:
        """Gets all the active rentals."""
        active_rental_ids = [rental_id for rental_id, bike_id in self._active_rentals.values()]
        return await Rental.filter(id__in=active_rental_ids).prefetch_related('updates', 'bike')

    async def active_rental(self, user: Union[User, int], *, with_locations=False) -> Union[Rental, Tuple]:
        """Gets the active rental for a given user."""
        if isinstance(user, int):
            user_id = user
        if isinstance(user, User):
            user_id = user.id

        rental_id, bike_id = self._active_rentals[user_id]
        rental = await Rental.filter(id=rental_id).first().prefetch_related('updates', 'bike')
        if with_locations:
            locations = await LocationUpdate.filter(bike_id=bike_id,
                                                    time__gte=rental.updates[0].time.strftime("%Y-%m-%d %H:%M:%S"))
            if locations:
                return rental, locations[0].location, locations[-1].location
            else:
                return rental, None, None
        else:
            return rental

    def has_active_rental(self, user: Union[User, int]) -> bool:
        """Checks if the given user has an active rental."""
        return (user if isinstance(user, int) else user.id) in self._active_rentals

    def is_active(self, rental_id):
        """Checks if the given rental ID is currently active."""
        return rental_id in {rental for rental, bike in self._active_rentals.values()}

    def is_in_use(self, bike: Union[Bike, int]) -> bool:
        """Checks if the given bike is in use."""
        bid = bike.id if isinstance(bike, Bike) else bike
        return any(bid == rental[1] for rental in self._active_rentals.values())

    def is_available(self, bike: Union[Bike, int], reservation_manager) -> bool:
        """A bike is available if the bike is un-rented and it is not reserved."""
        return not self.is_in_use(bike) and not reservation_manager.is_reserved(bike)

    def is_renting(self, user_id: int, bike_id: int) -> bool:
        """Checks if the given user is renting the given bike."""
        return user_id in self._active_rentals and self._active_rentals[user_id][1] == bike_id

    async def get_price_estimate(self, rental: Union[Rental, int]) -> float:
        """Gets the price of the rental so far."""
        if isinstance(rental, int):
            rental = await Rental.filter(id=rental).first()
        elif isinstance(rental, Rental):
            rental = rental

        return await get_price(rental.start_time, datetime.now())

    async def get_available_bikes(self, bike_ids: List[int]) -> List[Bike]:
        """Given a list of bike ids, checks if they are free or not and returns the ones that are free."""
        rental_ids = [rental_id for rental_id, bike_id in self._active_rentals.values()]
        if not bike_ids:
            return []

        query = Bike.filter(id__in=bike_ids)

        if rental_ids:
            query = query.filter(rentals__id__not_in=rental_ids)

        return await query.prefetch_related(Prefetch("updates", queryset=LocationUpdate.all().limit(100)))

    async def rebuild(self):
        """
        Rebuilds the currently active rentals from the database.
        """
        unfinished_rentals = await Rental.filter(
            updates__type__not_in=(t.value for t in RentalUpdateType.terminating_types()))
        for rental in unfinished_rentals:
            self._active_rentals[rental.user_id] = (rental.id, rental.bike_id)

    async def _resolve_target(self, target: Union[Rental, User]) -> Tuple[Rental, User]:
        """Given a rental or user, "resolves" the rental, user pair."""
        if isinstance(target, Rental):
            rental = target
            user = await User.filter(id=rental.user_id).first()
            if user.id not in self._active_rentals or not self._active_rentals[user.id][0] == rental.id:
                raise InactiveRentalError("Given rental is not the active rental for the user!")
        elif isinstance(target, User):
            user = target
            if user.id not in self._active_rentals:
                raise InactiveRentalError("Given user has no active rentals!")
            rental_id, bike_id = self._active_rentals[target.id]
            rental = await get_rental(rental_id)
        else:
            raise TypeError(f"Supplied target must be a Rental or User, not {type(target)}")

        return rental, user

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
