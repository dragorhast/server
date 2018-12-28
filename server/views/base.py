"""
The base view for the API. This view contains functionality
required in all other views.
"""

from typing import Optional

from aiohttp.web import View, UrlDispatcher


class ViewURLError(Exception):
    """
    Raised if the view doesn't provide a URL.
    """


class BaseView(View):
    """
    The base view that all other views extend. Contains some useful
    helper functions that the extending classes can use.

    .. todo:: Add CORS configuration to each view. Currently CORS is disabled.
    .. todo:: Add permissions so that views may limit functionality as needed.
    """

    url: str
    name: Optional[str]

    @classmethod
    def register(cls, router: UrlDispatcher, base: Optional[str] = None):
        """
        Registers the view with the given router.

        :raises ViewURLError: If the URL hasn't been set on the given view.
        """
        if cls.url is None:
            raise ViewURLError("No URL provided!")
        url = base + cls.url if base is not None else cls.url

        kwargs = {}
        name = getattr(cls, "name", None)
        if name is not None:
            kwargs["name"] = name

        router.add_view(url, cls, **kwargs)
