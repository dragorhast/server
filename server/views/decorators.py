"""
Decorators
-------------------------
"""
from enum import Enum
from functools import wraps
from inspect import isawaitable
from typing import Union, Any, Dict, Tuple

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_urldispatcher import View
from apispec.ext.marshmallow import OpenAPIConverter, resolver

from server.serializer import JSendStatus, JSendSchema


converter = OpenAPIConverter("3.0.2", resolver, None)


class Optional:
    """Signify the match map entry to be optional."""

    def __init__(self, value):
        self.value = value


class GetFrom(Enum):
    AUTH_HEADER = "Authorization"


def flatten(error):
    errors = []
    for sub_error in error.args:
        if isinstance(sub_error, Exception):
            errors += flatten(sub_error)
        else:
            errors.append(sub_error)
    return errors


def resolve_match_map(request: Request, match_map) -> Dict[str, Any]:
    resolved_matches = {}
    errors = []

    for key, value in match_map.items():

        if isinstance(value, Optional):
            value = value.value
            is_optional = True
        else:
            is_optional = False

        if isinstance(value, str):
            value = (value, int)

        if isinstance(value, tuple):
            try:
                param = request.match_info.get(value[0])
                if param is not None and is_optional:
                    continue
                resolved_matches[key] = value[1](param)
            except ValueError:
                errors.append(ValueError(
                    f'Could not convert url parameter "{param}" to expected type {value[1].__name__}.'))
        elif value == GetFrom.AUTH_HEADER:
            if "Authorization" not in request.headers:
                if not is_optional:
                    errors.append(ValueError("Missing Authorization header."))
                continue
            elif not request.headers["Authorization"].startswith("Bearer "):
                errors.append(ValueError("Malformed Authorization header (expected Bearer $TOKEN)."))
                continue
            user_id = request.app["token_verifier"].verify_token(request.headers["Authorization"][7:])
            resolved_matches[key] = user_id
        else:
            raise TypeError(f"match_getter incorrectly configured (doesn't support {type(value)})")

    if errors:
        raise ValueError(*errors)
    return resolved_matches


def match_getter(getter_function, *injection_parameters: Union[str, Optional],
                 **match_map: Union[str, GetFrom, Optional, Tuple[str, type]]):
    """
    Automatically fetches and includes an item, or 404's if it doesn't exist.

    .. code-block:: python

        # example usage
        @match_getter(Store.get_bike, bike, bike_id=id)
        async def get(self, bike: Bike)
            return web.json_response(data=bike.serialize())

    :param getter_function: The function to fetch the item from.
    :param injection_parameters: The name of the parameter to pass the object as.
    :param match_map: Associates a kwarg on the ``getter_function`` to a url variable, or
    :return: A decorator that wraps the response and passes in the object.
    """

    def attach_instance(original_function):

        @wraps(original_function)
        async def new_func(self: View, **kwargs):
            try:
                params = resolve_match_map(self.request, match_map)
            except (ValueError, TypeError) as error:
                response = {
                    "status": JSendStatus.FAIL,
                    "data": {
                        "message": "Errors with your request.",
                        "errors": flatten(error)
                    }
                }
                raise web.HTTPBadRequest(text=JSendSchema().dumps(response), content_type='application/json')
            item = getter_function(**params)
            if isawaitable(item):
                item = await item

            # if the getter function returns multiple items,
            # and there are multiple parameter names,
            # then set those keys in the decorated function
            if isinstance(injection_parameters, tuple) and isinstance(item, tuple) and len(injection_parameters) == len(
                item):
                optional_injected_kwargs = dict(zip(injection_parameters, item))
            else:
                optional_injected_kwargs = {injection_parameters[0]: item}

            not_found = []
            injected_kwargs = {}
            for key, item in optional_injected_kwargs.items():
                if item is None and not isinstance(key, Optional):
                    not_found.append(key)
                elif isinstance(key, Optional):
                    injected_kwargs[key.value] = item
                else:
                    injected_kwargs[key] = item

            if not_found:
                response = {
                    "status": JSendStatus.FAIL,
                    "data": {
                        "message": f'Could not find {", ".join(not_found)} with the given params.',
                        "params": params
                    }
                }
                raise web.HTTPNotFound(text=JSendSchema().dumps(response), content_type='application/json')

            return await original_function(self, **kwargs, **injected_kwargs)

        setup_apispec(new_func, original_function)

        return new_func

    def setup_apispec(new_func, original_function):
        """Set up the apispec documentation on the new function"""
        if not hasattr(original_function, "__apispec__"):
            new_func.__apispec__ = {"schemas": [], "responses": {}, "parameters": []}
        else:
            new_func.__apispec__ = original_function.__apispec__

        if not hasattr(original_function, "__schemas__"):
            new_func.__schemas__ = []
        else:
            new_func.__schemas__ = original_function.__schemas__

        json_schema = converter.schema2jsonschema(JSendSchema(only=("status", "data")))

        new_func.__apispec__["responses"]["404"] = {
            "description": "resource_missing",
            "content": {"application/json": {"schema": json_schema}}
        }

        if "400" not in new_func.__apispec__["responses"]:
            new_func.__apispec__["responses"]["400"] = {
                "description": "request_errors",
                "content": {"application/json": {"schema": json_schema}}
            }

    return attach_instance
