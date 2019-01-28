"""
Utilities
-------------------------
"""
from enum import Enum
from functools import wraps
from inspect import isawaitable
from typing import Union, Any, Dict, Tuple

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_urldispatcher import View

from server.serializer import JSendStatus, JSendSchema


class GetFrom(Enum):
    AUTH_HEADER = "Authorization"


def resolve_match_map(request: Request, match_map) -> Dict[str, Any]:
    resolved_matches = {}
    for key, value in match_map.items():
        if isinstance(value, str):
            resolved_matches[key] = int(request.match_info.get(value))
        elif isinstance(value, tuple):
            resolved_matches[key] = value[1](request.match_info.get(value[0]))
        elif value == GetFrom.AUTH_HEADER:
            if "Authorization" not in request.headers:
                raise ValueError("Missing Authorization header.")
            elif not request.headers["Authorization"].startswith("Bearer "):
                raise ValueError("Malformed Authorization header (expected Bearer $TOKEN).")
            user_id = request.app["token_verifier"].verify_token(request.headers["Authorization"][7:])
            resolved_matches[key] = user_id
        else:
            raise TypeError(f"match_getter only supports Union[str, GetFrom] not {type(value)}")
    return resolved_matches


def match_getter(getter_function, *injection_parameters: str, **match_map: Union[str, GetFrom, Tuple[str, type]]):
    """
    Automatically fetches and includes an item, or 404's if it doesn't exist.

    .. code-block:: python

        # example usage
        @getter(Store.get_bike, 'id', 'bike_id')
        async def get(self, bike: Bike)
            return web.json_response(data=bike.serialize())

    :param getter_function: The function to fetch the item from.
    :param injection_parameters: The name of the parameter to pass the object as.
    :param match_map: Associates a kwarg on the ``getter_function`` to a url variable, or
    :return: A decorator that wraps the response and passes in the object.

    ..todo:: only supports int at the moment
    """

    def attach_instance(decorated):
        """
        Attaches an instance of the.

        :param decorated:
        :return:
        """

        @wraps(decorated)
        async def new_func(self: View, **kwargs):
            try:
                params = resolve_match_map(self.request, match_map)
            except (ValueError, TypeError) as e:
                response = {
                    "status": JSendStatus.FAIL,
                    "data": {
                        "message": "Errors with your request.",
                        "errors": e.args
                    }
                }
                raise web.HTTPBadRequest(text=JSendSchema().dumps(response), content_type='application/json')
            item = getter_function(**params)
            if isawaitable(item):
                item = await item

            if item is None:
                response = {
                    "status": JSendStatus.FAIL,
                    "data": {
                        "message": f'Could not find needed {", ".join(injection_parameters)} with the given params.',
                        "params": params
                    }
                }
                raise web.HTTPNotFound(text=JSendSchema().dumps(response), content_type='application/json')

            # if the getter function returns multiple items,
            # and there are multiple parameter names,
            # then set those keys in the decorated function
            if isinstance(injection_parameters, tuple) and isinstance(item, tuple) and len(injection_parameters) == len(
                item):
                injected_kwargs = dict(zip(injection_parameters, item))
            else:
                injected_kwargs = {injection_parameters[0]: item}

            return await decorated(self, **kwargs, **injected_kwargs)

        return new_func

    return attach_instance
