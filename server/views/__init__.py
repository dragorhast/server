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

.. _`Web Api Design`: https://pages.apigee.com/rs/apigee/images/api-design-ebook-2012-03.pdf
.. _idempotent: https://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.1.2
"""

from aiohttp.web_urldispatcher import UrlDispatcher

from .bikes import *
from .issues import *
from .pickups import *
from .rentals import *
from .reservations import *
from .users import *
from .misc import send_to_developer_portal

views = [
    BikeView, BikesView, BikeRentalsView, BikeSocketView,
    IssuesView,
    PickupView, PickupsView, PickupBikesView, PickupReservationsView,
    RentalView, RentalsView,
    ReservationView, ReservationsView,
    UserView, UsersView, UserIssuesView, UserRentalsView, UserReservationsView
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
