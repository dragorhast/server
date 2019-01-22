"""
Utilities
-------------------------
"""
from collections import Iterable
from functools import wraps
from inspect import isawaitable

from aiohttp import web
from aiohttp.web_urldispatcher import View

from server.serializer import JSendStatus, JSendSchema


def match_getter(getter_function, *injection_parameters: str, **match_map):
    """
    Automatically fetches and includes an item, or 404's if it doesn't exist.

    .. code-block:: python

        # example usage
        @getter(Store.get_bike, 'id', 'bike_id')
        async def get(self, bike: Bike)
            return web.json_response(data=bike.serialize())

    :param getter_function: The function to fetch the item from.
    :param injection_parameters: The name of the parameter to pass the object as.
    :param match_map: Matches a request parameter key to the input variable on the getter_function
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
            params = {
                key: int(self.request.match_info.get(value))
                for key, value in match_map.items()
            }

            item = getter_function(**params)
            if isawaitable(item):
                item = await item

            if item is None:
                schema = JSendSchema()
                response = {
                    "status": JSendStatus.FAIL,
                    "data": {
                        "message": "Requested item does not exist."
                    }
                }

                raise web.HTTPNotFound(text=schema.dumps(response), content_type='application/json')

            # if the getter function returns multiple items,
            # and there are multiple parameter names,
            # then set those keys in the decorated function
            if isinstance(injection_parameters, tuple) and isinstance(item, tuple) and len(injection_parameters) == len(item):
                injected_kwargs = dict(zip(injection_parameters, item))
            else:
                injected_kwargs = {injection_parameters[0]: item}

            return await decorated(self, **kwargs, **injected_kwargs)

        return new_func

    return attach_instance
