"""
Decorators
----------

This module defines some decorators that significantly reduce
the boilerplate when handling JSON IO. These are used on the
routes of the system to gracefully serialize, deserialize, and
validate the data coming in and out of the app.

.. note:: Annotating a route with ``@expects(None)`` or ``@returns(None)``
    is purely for clarity and has no effect. It may however make the
    route definitions easier to read.
"""

from functools import wraps
from json import JSONDecodeError
from typing import Optional

from aiohttp import web
from aiohttp.web_urldispatcher import View
from marshmallow import Schema, ValidationError
from marshmallow_jsonschema import JSONSchema

from server.serializer import JSendSchema, JSendStatus


def expects(schema: Optional[Schema], into="data"):
    """
    A decorator that asserts that the JSON data supplied
    to the route validates the given :class:`~marshmallow.Schema`.

    It also handles missing data, malformed input, and invalid schemas.
    If the data is valid, it is stored on the request under the key
    supplied to the ``into`` parameter, otherwise it displays a
    descriptive error to the user.

    .. code:: python

        @expects(BikeSchema(), "my_data")
        async def get(self):
            valid_data = self.request["my_data"]

    :param schema: The schema to validate.
    :param into: The key to store the validated data in.
    """

    # if schema is none, then bypass the decorator
    if schema is None:
        return lambda x: x

    # assert the schema is of the right type
    if not isinstance(schema, Schema):
        raise TypeError

    json_schema = JSONSchema().dump(schema)["definitions"][type(schema).__name__]

    def decorator(original_function):

        @wraps(original_function)
        async def new_func(self: View, **kwargs):

            # if the request is not JSON or missing, return a warning and the valid schema
            if not self.request.body_exists or not self.request.content_type == "application/json":
                response_schema = JSendSchema()
                response_data = response_schema.dump({
                    "status": JSendStatus.FAIL,
                    "data": {
                        "message": f"This route ({self.request.method}: {self.request.rel_url}) only accepts JSON.",
                        "schema": json_schema
                    }
                })
                return web.json_response(response_data, status=400)

            try:
                self.request[into] = schema.load(await self.request.json())
            except JSONDecodeError as err:
                # if the data is not valid json, return a warning and the valid schema
                response_schema = JSendSchema()
                response_data = response_schema.dump({
                    "status": JSendStatus.FAIL,
                    "data": {"json": f"Could not parse supplied JSON ({', '.join(err.args)})."}
                })
                return web.json_response(response_data, status=400)
            except ValidationError as err:
                # if the json data does not match the schema, return the errors and the valid schema
                response_schema = JSendSchema()
                response_data = response_schema.dump({
                    "status": JSendStatus.FAIL,
                    "data": {
                        "errors": err.messages,
                        "schema": json_schema
                    }
                })
                return web.json_response(response_data, status=400)

            # if everything passes, execute the original function
            return await original_function(self, **kwargs)

        return new_func

    return decorator


def returns(schema: Optional[Schema]):
    """
    A decorator that asserts a the data returned
    from the route validates the given :class:`~marshmallow.Schema`.

    The data is dumped into the supplied schema, meaning
    as long as this decorator is applied to the route,
    it is possible to return plain python dictionaries.

    .. code:: python

        @returns(JSendSchema())
        async def get(self):
            result = await do_stuff()
            return {
                "status": JSendStatus.SUCCESS,
                "data": result
            }

    :param schema: The schema that the output data must conform to
    """

    # if schema is none, then bypass the decorator
    if schema is None:
        return lambda x: x

    # assert the schema is of the right type
    if not isinstance(schema, Schema):
        raise TypeError

    def decorator(original_function):

        @wraps(original_function)
        async def new_func(self: View, **kwargs):

            response_data = await original_function(self, **kwargs)

            try:
                return web.json_response(schema.dump(response_data))
            except ValidationError as err:
                response_schema = JSendSchema()
                response_data = response_schema.dump({
                    "status": JSendStatus.ERROR,
                    "data": err.messages,
                    "message": "We tried to send you data back, but it came out wrong."
                })
                return web.json_response(response_data, status=500)

        return new_func

    return decorator
