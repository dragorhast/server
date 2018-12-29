"""
This package contains the server API for viewing,
renting, reserving, and manipulating bikes.

API Conventions
---------------

The API conforms as best as possible to the REST standard. For a quick primer, look at `Web Api Design`_. In short,
the api must:

* Be ordered in terms of resources (nouns such as bike)
* Have multiple ways of accessing the same resource (GET, POST, PUT, PATCH, DELETE)
* Accept and return JSON with snake_case key naming
* Have idempotent_ GET, PUT, PATCH, and DELETE operations
* Support filtering (if necessary) using the query string

API Expected Responses
----------------------

The server responds with JSend formatted JSON to all GET, POST, and PUT requests.
DELETE requests respond with a 204 content not found.

.. _`Web Api Design`: https://pages.apigee.com/rs/apigee/images/api-design-ebook-2012-03.pdf
.. _idempotent: https://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.1.2
"""
from typing import List, Type

from aiohttp.web_routedef import UrlDispatcher

from server import logger
from server.views.base import BaseView
from .bikes import BikeView, BikesView, BikeRentalsView, BikeSocketView
from .issues import IssuesView
from .misc import send_to_developer_portal
from .pickups import PickupView, PickupsView, PickupBikesView, PickupReservationsView
from .rentals import RentalView, RentalsView
from .reservations import ReservationView, ReservationsView
from .users import UserView, UsersView, UserIssuesView, UserRentalsView, UserReservationsView, MeView

views: List[Type[BaseView]] = [
    BikeView, BikesView, BikeRentalsView, BikeSocketView,
    IssuesView,
    PickupView, PickupsView, PickupBikesView, PickupReservationsView,
    RentalView, RentalsView,
    ReservationView, ReservationsView,
    UserView, UsersView, UserIssuesView, UserRentalsView, UserReservationsView, MeView
]


def register_views(router: UrlDispatcher, base: str):
    """
    Registers all the API views onto the given router at a specific root url.

    :param router: The router to register the views to.
    :param base: The base URL.
    """
    for view in views:
        logger.info(f"Registered {view.__name__} at {base + view.url}")
        view.register(router, base)
