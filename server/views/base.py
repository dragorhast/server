from typing import Optional

from aiohttp.web import View, UrlDispatcher


class ViewURLException(Exception):
    pass


class BaseView(View):
    """
    The base view that all other views extend. Contains some useful
    helper functions that the extending classes can use.

    todo: allow CORS per-basis on each view
    todo: more granular permissions
    """

    url = None
    cors_allowed = False

    @classmethod
    def register(cls, router: UrlDispatcher, base: Optional[str] = None):
        """
        Registers the view with an router.

        :raises
        """
        if cls.url is None:
            raise ViewURLException("No url provided!")
        url = base + cls.url if base is not None else cls.url
        router.add_view(url, cls)