"""
Base
------------------------

The base view for the API. This view contains functionality
required in all other views.
"""

from typing import Optional

from aiohttp.abc import Application
from aiohttp.web import View, AbstractRoute
from aiohttp_cors import CorsConfig, CorsViewMixin, ResourceOptions

from server.service.bike_connection_manager import BikeConnectionManager
from server.service.rental_manager import RentalManager


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
    route: AbstractRoute
    rental_manager: RentalManager
    bike_connection_manager: BikeConnectionManager

    cors_config = {
        "*": ResourceOptions(
            allow_methods='*',
            allow_headers=('Authorization',)
        )
    }

    @classmethod
    def register_route(cls, app: Application, base: Optional[str] = None):
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

        cls.route = app.router.add_view(url, cls, **kwargs)
        cls.rental_manager = app["rental_manager"]
        cls.bike_connection_manager = app["bike_location_manager"]

    @classmethod
    def enable_cors(cls, cors: CorsConfig):
        """Enables CORS on the view."""
        try:
            cors.add(cls.route)
        except AttributeError as error:
            raise ViewConfigurationError("No route assigned. Please register the route first.") from error
