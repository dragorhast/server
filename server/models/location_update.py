"""
Location
---------------------------
"""

from tortoise import Model, fields
from tortoise.contrib.gis import gis_fields


class LocationUpdate(Model):
    """
    A location update places a bike
    at some set of coordinates
    at a specific point in time.
    """
    id = fields.IntField(pk=True)
    bike = fields.ForeignKeyField("models.Bike")
    location = gis_fields.PointField(srid=27700)
    time = fields.DatetimeField(auto_now_add=True)
