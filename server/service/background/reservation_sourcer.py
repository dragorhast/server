import heapq
from asyncio import sleep, gather
from collections import defaultdict
from datetime import timedelta, datetime, timezone
from typing import List, Tuple, Dict, Set

from server.models import PickupPoint
from server.service.manager.reservation_manager import ReservationManager, ReservationEvent, MINIMUM_RESERVATION_TIME


def is_within_reservation_time(date_pickup):
    date, pickup = date_pickup
    return date < datetime.now(timezone.utc) + MINIMUM_RESERVATION_TIME


class ReservationSourcer:
    """
    This background service keeps a track of reservations with missing bikes.
    """

    def __init__(self, reservation_manager: ReservationManager):
        reservation_manager.hub.subscribe(ReservationEvent.opened_reservation, self.opened_reservation)
        reservation_manager.hub.subscribe(ReservationEvent.cancelled_reservation, self.cancelled_reservation)
        self._reservation_manager = reservation_manager
        self._rental_heap: List[Tuple[datetime, PickupPoint]] = []
        self._shortages: Set[Tuple[datetime, PickupPoint]] = set()

    def shortages(self) -> Dict[PickupPoint, Tuple[int, datetime]]:
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
        """Runs the reservation notifier at most once every ``interval``."""
        if interval is None:
            interval = timedelta(minutes=1)

        while True:
            await gather(
                self._queue_shortages(),
                self._cull_shortages(),
                sleep(interval.total_seconds())
            )

    async def _queue_shortages(self):
        """
        For each reservation in the heap, check if it is within
        the reservation time and add it to the set of shortages
        if there is not a bike at that pickup to claim.
        """
        if not self._rental_heap:
            return

        while is_within_reservation_time(self._rental_heap[0]):
            time, pickup = heapq.heappop(self._rental_heap)

            if await self._reservation_manager.pickup_bike_surplus(pickup) < 0:
                self._shortages.add((time, pickup))

    async def _cull_shortages(self):
        """
        For each shortage, if bikes have been added to the pickup
        point, remove shortages from the set starting from the
        earliest shortage.
        """
        for pickup, shortage in self.shortages().items():
            stored_shortage_amount, closest_date = shortage
            surplus = await self._reservation_manager.pickup_bike_surplus(pickup)
            actual_storage_amount = -surplus

            if stored_shortage_amount > actual_storage_amount:
                # if more bikes have arrived...
                new_bikes = stored_shortage_amount - actual_storage_amount
                pickup_shortages = filter(lambda x: x[1] == pickup, self._shortages)
                closest_shortages = list(sorted(pickup_shortages, key=lambda x: x[0]))[:new_bikes]

                for shortage in closest_shortages:
                    # remove the shortages filled by the bikes
                    self._shortages.remove(shortage)

    def opened_reservation(self, pickup, user, time):
        if time < datetime.now(timezone.utc) + MINIMUM_RESERVATION_TIME:
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
