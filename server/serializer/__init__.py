"""
The serializer package houses all the schemas for the input/output in the system.
The serializers are used to generate and validate any raw data (such as JSON)
going in and out of the system.
"""

from server.serializer.models import BikeSchema, UserSchema, RentalSchema
from .fields import BytesField, EnumField
from .jsend import JSendSchema, JSendStatus
