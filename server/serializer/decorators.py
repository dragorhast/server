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
    A decorator that asserts the route accepts json data of a given schema.

    :param schema: The schema to validate.
    :param into: The key to store the validated data in.
    """

    if schema is not None and not isinstance(schema, Schema):
        raise TypeError

    def decorator(original_function):

        @wraps(original_function)
        async def new_func(self: View, **kwargs):

            if schema is None:
                return await original_function(self, **kwargs)

            json_schema = JSONSchema().dump(schema)["definitions"][type(schema).__name__]

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
            except ValidationError as err:
                response_schema = JSendSchema()
                response_data = response_schema.dump({
                    "status": JSendStatus.FAIL,
                    "data": {
                        "errors": err.messages,
                        "schema": json_schema
                    }
                })
                return web.json_response(response_data, status=400)
            except JSONDecodeError as err:
                response_schema = JSendSchema()
                response_data = response_schema.dump({
                    "status": JSendStatus.FAIL,
                    "data": {"json": f"Could not parse supplied JSON ({', '.join(err.args)})."}
                })
                return web.json_response(response_data, status=400)

            return await original_function(self, **kwargs)

        return new_func

    return decorator


def returns(schema: Optional[Schema]):
    """
    A decorator that asserts a route returns the given schema.
    It also properly returns it, meaning that as long as you
    have this decorator, you can return regular python dictionaries.

    :param schema: The schema that the output data
    """
    if schema is not None and not isinstance(schema, Schema):
        raise TypeError

    def decorator(original_function):

        @wraps(original_function)
        async def new_func(self: View, **kwargs):

            response_data = await original_function(self, **kwargs)

            if schema is None:
                return response_data

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
