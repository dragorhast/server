"""
Reservation Manager
===================

Handles the creation, removal, and updating of reservations.

Reservations are used to book a bike ahead of time, with some guarantees in place
to ensure that your bike will be in the location you need it to be when you need
it to be.

It operates on the concept of "slots" which are used to abstract away a rack.
A pickup point has a number of slots ie. the number of bikes currently in that
point. When a reservation is made, a slot is marked. Anyone who tries to rent
a bike from a pickup point with no slots left (ie, all bikes inside it are
reserved) will be denied.

Reservations can be claimed between one hour before and after the requested pickup
time. Sometimes there may not be a bike available if you come early. In that case,
just wait. The bike will arrive by your requested time.

Responsibilities
----------------

This object handles everything needed for bike reservations.

- add a reservation
- collect a reservation
- get reservations for a pickup point
"""
import random
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple, Set, Optional, List

from shapely.geometry import Point

from server.models import Reservation, PickupPoint, User, Bike, Rental
from server.models.reservation import ReservationOutcome
from server.service.access.reservations import create_reservation, current_reservation
from server.service.manager.bike_connection_manager import BikeConnectionManager
from server.service.manager.rental_manager import RentalManager, CurrentlyRentedError

MINIMUM_RESERVATION_TIME = timedelta(hours=3)
"""The minimum amount of time in the future a reservation must be made if there are no bikes there."""

RESERVATION_WINDOW = timedelta(hours=1)
"""The window of time a user has to claim a rental."""


class ReservationError(Exception):
    pass


class CollectionError(ReservationError):

    def __init__(self, message, reserved_for, reservation_window):
        self.message = message
        self.reserved_for = reserved_for
        self.reservation_window = reservation_window

    @property
    def lower_bound(self):
        return self.reserved_for - self.reservation_window / 2

    @property
    def upper_bound(self):
        return self.reserved_for + self.reservation_window / 2


class ReservationManager:

    def __init__(self, bike_connection_manager: BikeConnectionManager, rental_manager: RentalManager):
        self.reservations: Dict[int, Set[Tuple[int, datetime]]] = defaultdict(set)
        """Maps a pickup point to its reservations."""

        self.pickup_points: Set[PickupPoint] = set()
        self._bike_connection_manager = bike_connection_manager
        self._rental_manager = rental_manager

    async def reserve(self, user: User, pickup: PickupPoint, for_time: datetime) -> Reservation:
        """
        Reserves a bike at a pickup point.

        :raises ReservationError: If there are any issues with making the reservation.
        """
        if await current_reservation(user) is not None:
            raise ReservationError("User has reservation already.")

        if for_time - datetime.now(timezone.utc) < MINIMUM_RESERVATION_TIME:
            # ensure there is a bike there
            available_bikes = await self._available_bikes(pickup)
            if len(available_bikes) <= len(self.reservations[pickup.id]):
                raise ReservationError(
                    f"No available bikes in the requested point, and not enough time to source one (less than {MINIMUM_RESERVATION_TIME}).")

        reservation = await create_reservation(user, pickup, for_time)
        self.reservations[pickup.id].add((reservation.id, reservation.reserved_for))
        return reservation

    async def claim(self, reservation: Reservation, bike: Bike = None) -> Tuple[Rental, Point]:
        """
        Collects the bike for a given reservation, creating a rental.

        Collection can only happen 30 minutes before or after

        :param reservation: The reservation to collect.
        :param bike: Optionally the specific bike to collect.
        :raises CollectionError: If the bike is being picked up outside the reservation window.
        :raises ReservationError: If there are no bikes in the pickup point.
        :raises ActiveRentalError: If the user already has an active rental.
        :raises ValueError: If the pickup points
        """
        lower_bound = reservation.reserved_for - RESERVATION_WINDOW / 2
        upper_bound = reservation.reserved_for + RESERVATION_WINDOW / 2

        if datetime.now(timezone.utc) >= upper_bound:
            # todo delete reservation
            pass

        if not lower_bound <= datetime.now(timezone.utc) <= upper_bound:
            raise CollectionError(
                f"You may only collect a rental in a {RESERVATION_WINDOW} window around {reservation.reserved_for}.",
                reservation.reserved_for, RESERVATION_WINDOW
            )

        available_bikes = await self._available_bikes(reservation.pickup_point)
        if not available_bikes:
            raise ReservationError("No bikes at this pickup point.")

        if bike is None:
            bike = random.choice(available_bikes)  # nosec - using random.choice here is not a vulnerability

        pickup = self._pickup_containing(bike)
        if not pickup or pickup.id != reservation.pickup_point.id:
            raise CollectionError(
                "Requested bike is not in the pickup point of the reservation.",
                reservation.reserved_for,
                RESERVATION_WINDOW
            )

        if bike not in available_bikes:
            raise CurrentlyRentedError("Requested bike is currently being rented.", available_bikes)

        rental, start_location = await self._rental_manager.create(reservation.user, available_bikes[0])
        reservation.claimed_rental = rental
        await self._close_reservation(reservation, ReservationOutcome.CANCELLED)

        return rental, start_location

    async def cancel(self, reservation: Reservation):
        """
        Cancels a reservation.
        """
        await self._close_reservation(reservation, ReservationOutcome.CANCELLED)

    def reservations_in(self, pickup_point: int) -> List[int]:
        """Gets the reservation ids for a given pickup point."""
        return [id for id, time in self.reservations[pickup_point]]

    def is_reserved(self, bike: Bike) -> bool:
        """Checks if the given bike is reserved."""
        try:
            pickup = self._pickup_containing(bike)
        except ValueError:
            # the bike has no location updates. it can't be reserved
            return False

        if pickup is None:
            return False

        bikes = self._bike_connection_manager.bikes_in(pickup.area)
        return len(bikes) <= len(self.reservations[pickup.id])

    async def rebuild(self):
        """Rebuilds the reservation manager from the database."""
        unhandled_reservations = await Reservation.filter(outcome__isnull=True).prefetch_related("pickup_point")

        for reservation in unhandled_reservations:
            self.reservations[reservation.pickup_point.id].add((reservation.id, reservation.reserved_for))
            self.pickup_points.add(reservation.pickup_point)

    async def _close_reservation(self, reservation, outcome):
        self.reservations[reservation.pickup_point_id].remove((reservation.id, reservation.reserved_for))
        reservation.ended_at = datetime.now(timezone.utc)
        reservation.outcome = outcome
        await reservation.save()

    async def _available_bikes(self, pickup_point) -> List[Bike]:
        """Gets the available bikes in a pickup point."""
        bike_ids = self._bike_connection_manager.bikes_in(pickup_point.area)
        return await self._rental_manager.get_available_bikes(bike_ids)

    def _pickup_containing(self, bike: Bike) -> Optional[PickupPoint]:
        """Gets the pickup point the bike is currently in."""
        if not bike.updates:
            raise ValueError("No updates! Can't get location.")
        else:
            bike_location: Point = bike.updates[-1].location

        for point in self.pickup_points:
            if bike_location.within(point.area):
                return point

        return None
