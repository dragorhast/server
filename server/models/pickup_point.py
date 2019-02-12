"""
Pickup Point
---------------------------
"""

from typing import Iterable

from shapely.geometry import mapping, Polygon
from shapely.wkt import dumps
from tortoise import Model, fields
from tortoise.contrib.gis import gis_fields

from server.models import Bike
from server.serializer.geojson import GeoJSONType


class PickupPoint(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(255)
    area = gis_fields.PolygonField(srid=27700)

    def serialize(self):
        centroid = self.area.centroid

        return {
            "type": GeoJSONType.FEATURE,
            "geometry": mapping(self.area),
            "properties": {
                "name": self.name,
                "center": {"latitude": centroid.x, "longitude": centroid.y}
            }
        }
