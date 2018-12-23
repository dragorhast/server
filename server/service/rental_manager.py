"""
This module is what handles all the rentals in the system.
"""
from collections import defaultdict
from datetime import datetime
from typing import NamedTuple, Callable, Dict, Optional, Set

from server.models import User, Bike, RentalUpdate, RentalUpdateType
from server.serializer import RentalSchema


class Rental(NamedTuple):
    """An immutable rental handle. To modify, please use the rental manager."""
    user: User
    bike: Bike
    start_time: datetime = datetime.now()
    end_time: Optional[datetime] = None

    def _end(self):
        return Rental(self.user, self.bike, self.start_time, datetime.now())

    def serialize(self):
        schema = RentalSchema()

        rental_data = {
            "user": self.user,
            "bike": self.bike,
            "start_time": self.start_time,
        }

        if self.end_time:
            rental_data["end_time"] = self.end_time

        return schema.dump(rental_data)


class RentalManager:
    """
    Handles the lifecycle of the rental in the system.
    """

    _rentals: Dict[User, Rental] = {}
    _subscribers: Dict[Rental, Set[Callable]] = defaultdict(set)

    async def create(self, user: User, bike: Bike) -> Rental:
        """Creates a new rental for a user."""
        rental = Rental(user, bike)
        await self._publish_event(rental, RentalUpdateType.RENT)
        self._rentals[user] = rental
        return rental

    async def finish(self, rental: Rental):
        """Completes a rental."""
        await self._publish_event(rental, RentalUpdateType.RETURN)
        del self._rentals[rental.user]
        return rental._end()

    async def cancel(self, rental: Rental):
        """Cancels a rental, effective immediately, waiving the rental fee."""
        await self._publish_event(rental, RentalUpdateType.CANCEL)
        del self._rentals[rental.user]
        return rental._end()

    async def lock(self, rental: Rental, set_to: bool):
        """Locks a bike."""
        await self._publish_event(
            rental,
            RentalUpdateType.LOCK if set_to else RentalUpdateType.UNLOCK
        )

    async def _publish_event(self, rental, event_type: RentalUpdateType):
        await RentalUpdate.create(user=rental.user, bike=rental.bike, type=event_type)
        for subscriber in self._subscribers[rental]:
            subscriber(rental, event_type)

    def subscribe(self, rental: Rental, handler):
        """Subscribes a handler to a rental's events."""
        self._subscribers[rental].add(handler)

    def unsubscribe(self, rental: Rental, handler):
        """Unsubscribes a handler from a rental's events."""
        self._subscribers[rental].remove(handler)


rental_manager = RentalManager()
