"""
Pickup Point
---------------------------
"""
from datetime import datetime

from shapely.geometry import mapping
from tortoise import Model, fields
from tortoise.contrib.gis import gis_fields

from server.serializer.geojson import GeoJSONType


class PickupPoint(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(255)
    area = gis_fields.PolygonField(srid=27700)

    def serialize(self, reservation_manager, shortage_count: int = None, shortage_date: datetime = None):
        """
        Serializes a pickup point into a json format.

        :param shortage_count: The optional number of shortages.
        :param shortage_date: The optional date they need to be delivered by.
        """
        centroid = self.area.centroid

        data = {
            "type": GeoJSONType.FEATURE,
            "geometry": mapping(self.area),
            "properties": {
                "id": self.id,
                "name": self.name,
                "center": [centroid.x, centroid.y],
                "free_bikes": max(reservation_manager.pickup_bike_surplus(self), 0),
            }
        }

        if shortage_count is not None or shortage_date is not None:
            data["properties"]["shortage_count"] = shortage_count
            data["properties"]["shortage_date"] = shortage_date

        return data
