from functools import wraps

from aiohttp import web
from aiohttp.web_urldispatcher import View

from server.serializer import JSendStatus, JSendSchema


def getter(getter_function, var_name, key):
    """
    Automatically fetches and includes an item, or 404's if it doesn't exist.

    .. code-block:: python

        # example usage
        @getter(Store.get_bike, 'id', 'bike_id')
        async def get(self, bike: Bike)
            return web.json_response(data=bike.serialize())

    :param getter_function: The function to fetch the item from.
    :param var_name: The name of the url variable to extract.
    :param key: The key to filter in the function.
    :return: A decorator that wraps the response and passes in the object.
    """

    def attach_instance(decorated):
        """
        Attaches an instance of the.

        :param decorated:
        :return:
        """

        @wraps(decorated)
        async def new_func(self: View):
            item_id = int(self.request.match_info.get(var_name))
            item = await getter_function(**{key: item_id})
            if item is None:
                schema = JSendSchema()
                response = {
                    "status": JSendStatus.FAIL,
                    "data": {"id": f"Invalid {key} supplied"}
                }

                raise web.HTTPNotFound(text=schema.dumps(response), content_type='application/json')
            return await decorated(self, item)

        return new_func

    return attach_instance
