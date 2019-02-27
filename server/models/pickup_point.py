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

    def serialize(self, shortage_count: int = None, shortage_date: datetime = None):
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
                "center": {"latitude": centroid.x, "longitude": centroid.y}
            }
        }

        if shortage_count or shortage_date:
            data["shortage_count"] = shortage_count
            data["shortage_date"] = shortage_date

        return data
