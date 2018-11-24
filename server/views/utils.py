from functools import wraps

from aiohttp import web
from aiohttp.web_urldispatcher import View


def getter(getter_function, var_name):
    def attach_instance(decorated):
        """
        Attaches an instance of the.
        :param decorated:
        :return:
        """

        @wraps(decorated)
        def new_func(self: View):
            item_id = int(self.request.match_info.get(var_name))
            item = getter_function(item_id)
            if item is None:
                raise web.HTTPNotFound(reason="No item with that id.")
            return decorated(self, item)

        return new_func

    return attach_instance
