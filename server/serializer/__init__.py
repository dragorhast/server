"""
The serializer package houses all the schemas for the input/output in the system.
The serializers are used to generate and validate any raw data (such as JSON)
going in and out of the system.

.. note:: Unfortunately marshmallow does not play well with sphinx-autodoc,
    stripping out the :class:`~marshmallow.fields.Field` declarations from
    the schema definition. This can be fixed quite easily, however even if
    fixed, the :func:`repr` value on marshmallow fields is utterly useless..
    For that reason, it is recommended that you look at the code directly.
"""

from server.serializer.models import BikeSchema, UserSchema, RentalSchema
from .fields import Bytes, EnumField
from .jsend import JSendSchema, JSendStatus
