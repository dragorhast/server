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

from datetime import datetime
from typing import Dict, Union, Tuple, List

from shapely.geometry import Point
from tortoise.query_utils import Prefetch

from server.events import EventHub, EventList
from server.models import Bike, Rental, User, RentalUpdate, LocationUpdate
from server.models.issue import IssueStatus, Issue
from server.models.util import RentalUpdateType
from server.pricing import get_price
from server.service.access.rentals import get_rental_with_distance
from server.service.rebuildable import Rebuildable


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


class RentalEvent(EventList):

    def rental_started(self, user: User, bike: Bike, location: Point):
        """A new rental was started."""

    def rental_ended(self, user: User, bike: Bike, location: Point, price: float, distance: float):
        """A rental was ended."""

    def rental_cancelled(self, user: User, bike: Bike):
        """A rental was cancelled."""


class RentalManager(Rebuildable):
    """
    Handles the lifecycle of the rental in the system.

    Also publishes events on its hub, so that other modules can stay up to date with the system.
    When the module starts, it will replay all events from midnight that night.
    """

    def __init__(self):
        self._active_rentals: Dict[int, Tuple[int, int]] = {}
        """Maps user ids to a tuple containing their current rental and current bike."""

        self.hub = EventHub(RentalEvent)

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

        self.hub.emit(RentalEvent.rental_started, user, bike, current_location.location)

        return rental, current_location.location if current_location is not None else None

    async def finish(self, user: User, *, extra_cost=0.0) -> Rental:
        """
        Completes a rental.

        :raises InactiveRentalError: When there is no active rental for that user, or the given rental is not active.
        """
        rental, distance = await self._get_rental_with_distance(user)
        rental.price = await get_price(rental.updates[0].time, rental.updates[-1].time, extra_cost)

        current_location = await LocationUpdate.filter(bike_id=rental.bike_id).first()

        del self._active_rentals[user.id]
        await rental.save()
        await self._publish_event(rental, RentalUpdateType.RETURN)

        self.hub.emit(RentalEvent.rental_ended, user, rental.bike, current_location.location, rental.price, distance)

        return rental

    async def cancel(self, user: User) -> Rental:
        """Cancels a rental, effective immediately, waiving the rental fee."""
        rental, distance = await self._get_rental_with_distance(user)

        await self._publish_event(rental, RentalUpdateType.CANCEL)
        self.hub.emit(RentalEvent.rental_cancelled, user, rental.bike)

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

        return await query.prefetch_related(
            Prefetch("location_updates", queryset=LocationUpdate.all().limit(100)),
            "state_updates",
            Prefetch("issues", queryset=Issue.filter(status__not=IssueStatus.CLOSED))
        )

    async def _rebuild(self):
        """
        Rebuilds the currently active rentals from the database.

        Also replays events that happened today for use by subscribers.
        """
        unfinished_rentals = await Rental.filter(
            updates__type__not_in=(t.value for t in RentalUpdateType.terminating_types())
        )

        for rental in unfinished_rentals:
            self._active_rentals[rental.user_id] = (rental.id, rental.bike_id)

        midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        todays_updates = await RentalUpdate.filter(time__gt=midnight).prefetch_related("rental", "rental__user",
                                                                                       "rental__bike")

        for update in todays_updates:
            if update.type == RentalUpdateType.RENT:
                self.hub.emit(RentalEvent.rental_started, update.rental.user, update.rental.bike, None)  # todo location
            elif update.type == RentalUpdateType.RETURN:
                self.hub.emit(RentalEvent.rental_ended, update.rental.user, update.rental.bike, None, update.rental.price, None)
            elif update.type == RentalUpdateType.CANCEL:
                self.hub.emit(RentalEvent.rental_cancelled, update.rental.user, update.rental.bike)

    async def _get_rental_with_distance(self, user: User) -> Tuple[Rental, float]:
        """Given a rental or user, "resolves" the rental, user pair."""
        if not isinstance(user, User):
            raise TypeError(f"Supplied target must be a Rental or User, not {type(user)}")

        if user.id not in self._active_rentals:
            raise InactiveRentalError("Given user has no active rentals!")
        rental_id, bike_id = self._active_rentals[user.id]
        rental, distance = await get_rental_with_distance(rental_id)

        return rental, distance

    @staticmethod
    async def _publish_event(rental: Rental, event_type: RentalUpdateType):
        update = await RentalUpdate.create(rental=rental, type=event_type)

        if rental.updates._fetched:
            rental.updates.related_objects.append(update)
