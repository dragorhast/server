"""
GeoJSON Schema
--------------

Implements serializers for GEOJson objects, which is the format
through which the api communicates spacial data.
"""
from enum import Enum
from typing import Optional

from marshmallow import Schema, validates_schema, ValidationError
from marshmallow.fields import Dict, Raw, Nested

from server.serializer.fields import EnumField


class GeoJSONType(str, Enum):
    FEATURE = "Feature"
    FEATURE_COLLECTION = "FeatureCollection"


class GeometryType(str, Enum):
    POINT = "Point"
    MULTIPOINT = "MultiPoint"
    LINESTRING = "LineString"
    MULTILINESTRING = "MultiLineString"
    POLYGON = "Polygon"
    MULTIPOLYGON = "MultiPolygon"
    GEOMETRYCOLLECTION = "GeometryCollection"


class Geometry(Schema):
    type = EnumField(GeometryType)
    coordinates = Raw()


class GeoJSON(Schema):

    def __init__(self, feature_type: Optional[GeoJSONType] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature_type = feature_type

    type = EnumField(GeoJSONType)
    properties = Dict()
    features = Nested('self', many=True)
    geometry = Nested(Geometry)

    @validates_schema
    def assert_correct_fields_included(self, data):
        if data["type"] == GeoJSONType.FEATURE and "geometry" not in data:
            raise ValidationError("All features must have geometry associated with it.")
        if data["type"] == GeoJSONType.FEATURE_COLLECTION and "features" not in data:
            raise ValidationError("All feature collections must have a list of features.")

    @validates_schema
    def assert_correct_type(self, data):
        if self.feature_type is not None and data["type"] != self.feature_type:
            raise ValidationError(f"Supplied schema is type {data['type']}, not {self.feature_type}.")

    @staticmethod
    def of(properties_schema: Schema, feature_type: Optional[GeoJSONType] = None, *args, **kwargs):
        """
        Creates a subclass of GeoJSON of a specific properties type.

        This allows us to require the ``properties`` property to be of a specific schema.
        """

        class TypedJSendSchema(GeoJSON):
            properties = Nested(properties_schema, *args, **kwargs)

        return TypedJSendSchema(feature_type)
