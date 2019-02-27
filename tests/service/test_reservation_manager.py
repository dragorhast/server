from datetime import datetime, timedelta, timezone

import pytest
from shapely.geometry import Point

from server.models import Reservation
from server.service.manager.rental_manager import CurrentlyRentedError
from server.service.manager.reservation_manager import ReservationError, CollectionError


class TestReservationManager:

    async def test_reserve(self, reservation_manager, random_user, random_pickup_point):
        """Assert that creating a reservation adds it to the database."""
        reservation = await reservation_manager.reserve(
            random_user, random_pickup_point, datetime.now(timezone.utc) + timedelta(hours=5)
        )

        reservations = await Reservation.all()
        assert len(reservations) == 1
        assert reservation in reservations

    async def test_reserve_close(self, reservation_manager, random_user, random_pickup_point):
        """Assert that creating a reservation in less than 3 hours from now fails if there are no bikes."""
        with pytest.raises(ReservationError) as e:
            reservation = await reservation_manager.reserve(
                random_user, random_pickup_point, datetime.now(timezone.utc) + timedelta(hours=2)
            )
        assert any("No available bikes" in arg for arg in e.value.args)

    async def test_reserve_close_free_bike(
        self, reservation_manager, bike_connection_manager,
        random_user_factory, random_pickup_point, random_bike
    ):
        """Assert that rentals in less than 3 hours with a free bike pass."""
        await bike_connection_manager.update_location(random_bike, random_pickup_point.area.centroid)

        reservation = await reservation_manager.reserve(
            await random_user_factory(), random_pickup_point, datetime.now(timezone.utc) + timedelta(hours=2)
        )

        reservations = await Reservation.all()
        assert len(reservations) == 1
        assert reservation in reservations

    async def test_collect(
        self, reservation_manager, bike_connection_manager,
        random_user, random_pickup_point, random_bike
    ):
        """Assert that collecting a rental creates one."""
        bike_connection_manager.is_connected = lambda x: True

        await bike_connection_manager.update_location(random_bike, random_pickup_point.area.centroid)
        reservation_manager.pickup_points.add(random_pickup_point)
        await reservation_manager.reserve(
            random_user, random_pickup_point, datetime.now(timezone.utc) + timedelta(minutes=10)
        )

        rental = await reservation_manager.claim(random_user, random_bike)

        assert not reservation_manager.reservations[random_pickup_point.id]
        assert rental[0].bike == random_bike

    async def test_collect_outside_window(
        self, reservation_manager, bike_connection_manager,
        random_user, random_pickup_point, random_bike
    ):
        """Assert that trying to collect outside the reservation window fails."""
        await bike_connection_manager.update_location(random_bike, random_pickup_point.area.centroid)
        reservation_manager.pickup_points.add(random_pickup_point)
        reservation = await reservation_manager.reserve(
            random_user, random_pickup_point, datetime.now(timezone.utc) + timedelta(hours=1, minutes=30)
        )

        with pytest.raises(CollectionError):
            rental = await reservation_manager.claim(random_user, random_bike)

    async def test_collect_no_bikes(
        self, reservation_manager, bike_connection_manager,
        random_user, random_pickup_point, random_bike
    ):
        """Assert that trying to collect from a pickup point with no bikes fails."""
        await bike_connection_manager.update_location(random_bike, random_pickup_point.area.centroid)
        reservation_manager.pickup_points.add(random_pickup_point)
        await reservation_manager.reserve(
            random_user, random_pickup_point, datetime.now(timezone.utc) + timedelta(minutes=20)
        )

        await bike_connection_manager.update_location(random_bike, Point(1000, 1000))

        with pytest.raises(ReservationError):
            await reservation_manager.claim(random_user, random_bike)

    async def test_collect_currently_rented_bike(
        self, reservation_manager, bike_connection_manager,
        random_user, random_pickup_point, random_bike_factory, rental_manager, random_admin
    ):
        """
        Assert that trying to collect a bike that is currently
        being rented fails, and returns bikes that are free.
        """
        bike_connection_manager.is_connected = lambda x: True

        used_bike = await random_bike_factory()
        available_bike = await random_bike_factory()
        reservation_manager.pickup_points.add(random_pickup_point)

        await bike_connection_manager.update_location(used_bike, random_pickup_point.area.centroid)
        await bike_connection_manager.update_location(available_bike, random_pickup_point.area.centroid)

        await reservation_manager.reserve(
            random_user, random_pickup_point, datetime.now(timezone.utc) + timedelta(minutes=20)
        )

        await rental_manager.create(random_admin, used_bike)

        with pytest.raises(CurrentlyRentedError) as e:
            rental = await reservation_manager.claim(random_user, used_bike)

        assert available_bike in e.value.available_bikes

    async def test_collect_bike_not_in_pickup(
        self, random_bike_factory, random_pickup_point, bike_connection_manager,
        reservation_manager, random_user
    ):
        """Assert that collecting a bike that isn't in the correct pickup point fails."""

        close_bike = await random_bike_factory()
        far_bike = await random_bike_factory()

        await bike_connection_manager.update_location(close_bike, random_pickup_point.area.centroid)
        await bike_connection_manager.update_location(far_bike, Point(100, 100))

        reservation_manager.pickup_points.add(random_pickup_point)
        await reservation_manager.reserve(
            random_user, random_pickup_point, datetime.now(timezone.utc) + timedelta(minutes=20)
        )

        with pytest.raises(CollectionError):
            await reservation_manager.claim(random_user, far_bike)

    async def test_bike_is_reserved(
        self, random_bike_factory, reservation_manager, random_pickup_point,
        bike_connection_manager, random_user_factory
    ):
        """
        Assert that if there are the same or more reservations as there are bikes
        in a pickup point that all the bikes are considered "reserved".
        """
        bike_connection_manager.is_connected = lambda x: True

        first = await random_bike_factory()
        second = await random_bike_factory()

        first_user = await random_user_factory()
        second_user = await random_user_factory()

        reservation_manager.pickup_points.add(random_pickup_point)
        await bike_connection_manager.update_location(first, random_pickup_point.area.centroid)
        await bike_connection_manager.update_location(second, random_pickup_point.area.centroid)

        assert not reservation_manager.is_reserved(first)
        assert not reservation_manager.is_reserved(second)

        await reservation_manager.reserve(
            first_user, random_pickup_point, datetime.now(timezone.utc) + timedelta(minutes=20)
        )

        assert not reservation_manager.is_reserved(first)
        assert not reservation_manager.is_reserved(second)

        await reservation_manager.reserve(
            second_user, random_pickup_point, datetime.now(timezone.utc) + timedelta(minutes=20)
        )

        assert reservation_manager.is_reserved(first)
        assert reservation_manager.is_reserved(second)
