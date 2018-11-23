"""
Makes the appropriate views available from the module.
"""
from aiohttp.web_urldispatcher import UrlDispatcher

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


def register_all(router: UrlDispatcher, base: str):
    for view in views:
        print("Registering "+str(view))
        view.register(router, base)
