import heapq
from asyncio import sleep
from collections import defaultdict
from datetime import timedelta, datetime
from typing import List, Tuple, Dict, Set

from server.models import PickupPoint
from server.service.manager.reservation_manager import ReservationManager, ReservationEvent, MINIMUM_RESERVATION_TIME


def is_within_reservation_time(date_pickup):
    date, pickup = date_pickup
    return date < datetime.now() + MINIMUM_RESERVATION_TIME


class ShortageNotifier:
    """
    This background service keeps a track of reservations with missing bikes.
    """

    def __init__(self, reservation_manager: ReservationManager):
        reservation_manager.hub.subscribe(ReservationEvent.new_reservation, self.new_reservation)
        reservation_manager.hub.subscribe(ReservationEvent.cancelled_reservation, self.cancelled_reservation)
        self._reservation_manager = reservation_manager
        self._rental_heap: List[Tuple[datetime, PickupPoint]] = []
        self._shortages: Set[Tuple[datetime, PickupPoint]] = set()

    async def shortages(self) -> Dict[PickupPoint, Tuple[int, datetime]]:
        """
        Gets a dictionary mapping all the pickup points with shortages
        to the number of bikes needed and the time they are needed by.
        """
        shortages = defaultdict(lambda: (0, datetime.max))
        for date, pickup in self._shortages:
            count, closest_date = shortages[pickup]
            closest_date = min(closest_date, date)
            shortages[pickup] = (count + 1, closest_date)
        return shortages

    async def run(self, interval: timedelta = None):
        """Runs the reservation notifier."""

        while True:
            while is_within_reservation_time(self._rental_heap[0]):
                time, pickup = heapq.heappop(self._rental_heap)

                if await self._reservation_manager.pickup_bike_surplus(pickup) < 0:
                    self._shortages.add((time, pickup))

            await sleep(interval.total_seconds())

    def new_reservation(self, pickup, user, time):
        if time < datetime.now() + MINIMUM_RESERVATION_TIME:
            # we know that there is a bike there
            return

        heapq.heappush(self._rental_heap, (time, pickup))

    def cancelled_reservation(self, pickup, user, time):
        """
        If a reservation is cancelled, we try to remove it.
        It doesn't matter if it doesn't exist, all we care about is that it is no longer there."""
        try:
            self._rental_heap.remove((time, pickup))
        except ValueError:
            pass
