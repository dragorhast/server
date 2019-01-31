from datetime import datetime

from shapely.geometry import Point


class TestBikeSerializer:

    def test_serializer_available(self, random_bike, rental_manager, bike_connection_manager):
        """Assert that a bike that is available includes its location."""
        rental_manager.is_available = lambda x: True
        bike_connection_manager.is_connected = lambda x: True
        bike_connection_manager.most_recent_location = lambda x: (Point(0, 0), datetime.now(), None)

        data = random_bike.serialize(bike_connection_manager, rental_manager)
        assert "current_location" in data
        assert "properties" not in data["current_location"]

    def test_serializer_unavailable(self, random_bike, rental_manager, bike_connection_manager):
        """Assert that a bike that is unavailable does not include its location."""
        rental_manager.is_available = lambda x: False
        bike_connection_manager.is_connected = lambda x: True
        bike_connection_manager.most_recent_location = lambda x: (Point(0, 0), datetime.now(), None)

        data = random_bike.serialize(bike_connection_manager, rental_manager)
        assert "current_location" not in data

    def test_serializer_force_location(self, random_bike, rental_manager, bike_connection_manager):
        rental_manager.is_available = lambda x: False
        bike_connection_manager.is_connected = lambda x: True
        bike_connection_manager.most_recent_location = lambda x: (Point(0, 0), datetime.now(), None)

        data = random_bike.serialize(bike_connection_manager, rental_manager, force_location=True)
        assert "current_location" in data

    def test_serializer_with_pickup(self, random_bike, rental_manager, bike_connection_manager, random_pickup_point):
        rental_manager.is_available = lambda x: True
        bike_connection_manager.is_connected = lambda x: True
        bike_connection_manager.most_recent_location = lambda x: (Point(0, 0), datetime.now(), random_pickup_point)

        data = random_bike.serialize(bike_connection_manager, rental_manager)
        assert data["current_location"]["properties"]["pickup_point"] == random_pickup_point.name
