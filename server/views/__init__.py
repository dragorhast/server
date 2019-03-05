"""
.. autoclasstree:: server.views

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

import aiohttp_cors
from aiohttp.abc import Application

from server import logger
from server.views.reports import AnnualReportView, MonthlyReportView, DailyReportView
from .bikes import BikeView, BikesView, BikeRentalsView, BikeSocketView, BikeIssuesView, BrokenBikesView, LowBikesView
from .issues import IssuesView, IssueView
from .misc import redoc, logo
from .pickups import PickupView, PickupsView, PickupBikesView, PickupReservationsView, PickupShortagesView
from .rentals import RentalView, RentalsView
from .reservations import ReservationView, ReservationsView
from .users import UserView, UsersView, UserIssuesView, UserRentalsView, UserReservationsView, MeView, \
    UserCurrentRentalView, UserCurrentReservationView, UserEndCurrentRentalView, UserPaymentView

views = [
    BikeView, BikesView, BrokenBikesView, LowBikesView, BikeRentalsView, BikeIssuesView, BikeSocketView,
    IssuesView, IssueView,
    PickupView, PickupsView, PickupBikesView, PickupReservationsView, PickupShortagesView,
    RentalView, RentalsView,
    ReservationView, ReservationsView,
    MeView, UserView, UsersView, UserIssuesView, UserRentalsView, UserCurrentRentalView, UserReservationsView, UserPaymentView,
    UserCurrentReservationView, UserEndCurrentRentalView,
    AnnualReportView, MonthlyReportView, DailyReportView
]


def register_views(app: Application, base: str):
    """
    Registers all the API views onto the given router at a specific root url.

    :param app: The app to register the views to.
    :param base: The base URL.
    """
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*",
        )
    })

    for view in views:
        logger.info("Registered %s at %s", view.__name__, base + view.url)
        view.register_route(app, base)
        view.enable_cors(cors)
