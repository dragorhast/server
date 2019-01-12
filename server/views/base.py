"""
The base view for the API. This view contains functionality
required in all other views.
"""

from typing import Optional

from aiohttp.web import View, UrlDispatcher, AbstractRoute
from aiohttp_cors import CorsConfig, CorsViewMixin, ResourceOptions

from server.permissions import Permission


class ViewConfigurationError(Exception):
    """
    Raised if the view doesn't provide a URL.
    """


class BaseView(View, CorsViewMixin):
    """
    The base view that all other views extend. Contains some useful
    helper functions that the extending classes can use.
    """

    url: str
    name: Optional[str]
    permissions: Optional[Permission]
    route: AbstractRoute

    cors_config = {
        "*": ResourceOptions(
            allow_methods='*',
            allow_headers=('Authorization',)
        )
    }

    @classmethod
    def register_route(cls, router: UrlDispatcher, base: Optional[str] = None):
        """
        Registers the view with the given router.

        :raises ViewConfigurationError: If the URL hasn't been set on the given view.
        """
        try:
            url = base + cls.url if base is not None else cls.url
        except AttributeError:
            raise ViewConfigurationError("No URL provided!")

        kwargs = {}
        name = getattr(cls, "name", None)
        if name is not None:
            kwargs["name"] = name

        cls.route = router.add_view(url, cls, **kwargs)

    @classmethod
    def enable_cors(cls, cors: CorsConfig):
        """Enables CORS on the view."""
        try:
            cors.add(cls.route)
        except AttributeError as error:
            raise ViewConfigurationError("No route assigned. Please register the route first.") from error
