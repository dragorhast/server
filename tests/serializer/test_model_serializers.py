from datetime import datetime

from shapely.geometry import Point


class TestBikeSerializer:

    def test_serializer_available(self, random_bike, rental_manager, bike_connection_manager, reservation_manager):
        """Assert that a bike that is available includes its location."""
        rental_manager.is_available = lambda x, y: True
        bike_connection_manager.is_connected = lambda x: True
        bike_connection_manager.most_recent_location = lambda x: (Point(0, 0), datetime.now(), None)
        bike_connection_manager.battery_level = lambda x: 100
        bike_connection_manager.is_locked = lambda x: True

        data = random_bike.serialize(bike_connection_manager, rental_manager, reservation_manager)
        assert "current_location" in data
        assert data["current_location"]["properties"]["pickup_point"] is None

    def test_serializer_unavailable(self, random_bike, rental_manager, bike_connection_manager, reservation_manager):
        """Assert that a bike that is unavailable does not include its location."""
        rental_manager.is_available = lambda x, y: False
        bike_connection_manager.is_connected = lambda x: True
        bike_connection_manager.most_recent_location = lambda x: (Point(0, 0), datetime.now(), None)
        bike_connection_manager.battery_level = lambda x: 100
        bike_connection_manager.is_locked = lambda x: True

        data = random_bike.serialize(bike_connection_manager, rental_manager, reservation_manager)
        assert "current_location" not in data

    def test_serializer_force_location(self, random_bike, rental_manager, bike_connection_manager, reservation_manager):
        rental_manager.is_available = lambda x, y: False
        bike_connection_manager.is_connected = lambda x: True
        bike_connection_manager.most_recent_location = lambda x: (Point(0, 0), datetime.now(), None)
        bike_connection_manager.battery_level = lambda x: 100
        bike_connection_manager.is_locked = lambda x: True

        data = random_bike.serialize(bike_connection_manager, rental_manager, reservation_manager, include_location=True)
        assert "current_location" in data

    def test_serializer_with_pickup(
        self, random_bike, rental_manager, bike_connection_manager, random_pickup_point, reservation_manager
    ):
        rental_manager.is_available = lambda x, y: True
        bike_connection_manager.is_connected = lambda x: True
        bike_connection_manager.most_recent_location = lambda x: (Point(0, 0), datetime.now(), random_pickup_point)
        bike_connection_manager.battery_level = lambda x: 100
        bike_connection_manager.is_locked = lambda x: True

        data = random_bike.serialize(bike_connection_manager, rental_manager, reservation_manager)
        assert data["current_location"]["properties"]["pickup_point"]["properties"]["name"] == random_pickup_point.name


class TestRentalSerializer:

    async def test_serializer(self, random_bike, random_user, rental_manager, bike_connection_manager, reservation_manager):
        await bike_connection_manager.update_location(random_bike, Point(0, 0))
        rental, location = await rental_manager.create(random_user, random_bike)
        rental_data = await rental.serialize(rental_manager, bike_connection_manager, reservation_manager, current_location=location)
