"""
Contains all the API views for the server.
"""

from aiohttp.web_urldispatcher import UrlDispatcher

from server import logger
from .bikes import *
from .issues import *
from .pickups import *
from .rentals import *
from .reservations import *
from .users import *

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
        logger.info(f"Registered {view.__name__} at {base+view.url}")
        view.register(router, base)
