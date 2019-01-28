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
from http import HTTPStatus
from json import JSONDecodeError
from typing import Optional, Tuple, Union, Dict

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
                return web.json_response(response_data, status=HTTPStatus.BAD_REQUEST)

            try:
                self.request[into] = schema.load(await self.request.json())
            except JSONDecodeError as err:
                # if the data is not valid json, return a warning
                response_schema = JSendSchema()
                response_data = response_schema.dump({
                    "status": JSendStatus.FAIL,
                    "data": {
                        "message": f"Could not parse supplied JSON.",
                        "errors": err.args
                    }
                })
                return web.json_response(response_data, status=HTTPStatus.BAD_REQUEST)
            except ValidationError as err:
                # if the json data does not match the schema, return the errors and the valid schema
                response_schema = JSendSchema()
                response_data = response_schema.dump({
                    "status": JSendStatus.FAIL,
                    "data": {
                        "message": "The request did not validate properly.",
                        "errors": err.messages,
                        "schema": json_schema
                    }
                })
                return web.json_response(response_data, status=HTTPStatus.BAD_REQUEST)

            # if everything passes, execute the original function
            return await original_function(self, **kwargs)

        return new_func

    return decorator


def returns(
    schema: Optional[Schema] = None, return_code: HTTPStatus = HTTPStatus.OK,
    **named_schema: Union[Schema, Tuple[Schema, HTTPStatus]]
):
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
    :param return_code: The code to return
    :param named_schema: Schema names, paired with their schema and return values.
    """

    # if no schema is defined, pass through
    if schema is None and not named_schema:
        return lambda x: x

    # add the schema passed via the args to the named_schema
    named_schema[None] = (schema, return_code)

    def decorator(original_function):

        @wraps(original_function)
        async def new_func(self: View, **kwargs):

            if schema:
                schema_name, response_data = None, await original_function(self, **kwargs)
            else:
                schema_name, response_data = await original_function(self, **kwargs)

            try:
                matched_schema = named_schema[schema_name]
                # if the named schema includes a return code as well, unwrap it
                if isinstance(matched_schema, tuple):
                    matched_schema, matched_return_code = matched_schema
                else:
                    matched_schema, matched_return_code = matched_schema, return_code
                return web.json_response(matched_schema.dump(response_data), status=matched_return_code)
            except (ValidationError, KeyError) as err:
                response_schema = JSendSchema()
                response_data = response_schema.dump({
                    "status": JSendStatus.ERROR,
                    "data": err.messages if isinstance(err, ValidationError) else err.args,
                    "message": "We tried to send you data back, but it came out wrong.",
                    "code": "test"
                })
                return web.json_response(response_data, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        return new_func

    return decorator
