"""
Rentals
-------
"""
from datetime import datetime
from typing import Union, Optional, Tuple, List

from shapely.geometry import LineString

from server.models import Bike, Rental, User
from server.models.util import RentalUpdateType


async def get_rentals_for_bike(bike: Union[int, Bike]):
    """
    Gets rentals for a given bike.

    :param bike: The bike or id to fetch.
    :return: An iterable of rentals.
    """
    if isinstance(bike, Bike):
        bid = bike.id
    elif isinstance(bike, int):
        bid = bike
    else:
        raise TypeError("Must be bike id or bike.")

    return await Rental.filter(bike__id=bid).prefetch_related('updates', 'bike')


async def get_rentals(*, user: User = None):
    if user:
        return await Rental.filter(user=user).prefetch_related('updates', 'bike')
    return await Rental.all().prefetch_related('updates', 'bike')


async def get_rental(rental_id: int) -> Rental:
    return await Rental.filter(id=rental_id).first().prefetch_related('updates', 'bike')


async def get_rental_with_distance(rental: Union[Rental, int]) -> Union[
    Tuple[Rental, Optional[float]], List[Tuple[Rental, float]], None]:
    """
    Gets the rentals along with their rental updates from the database. The query inner joins on location update
    and rental update, aggregating on the distance between the various location updates. This gives us our distance.
    At that point, we iterate through all the rentals with their updates, adding each update and emulating the
    "prefetch_related" functionality, since the location updates are needed in the rest of the system to get rental
    start and end.

    :param rental: The rental or rental ID you wish to get.
    :returns: A tuple containing the rental and its distance.

    .. note:: Works with both PostGIS and Spatialite
    """

    if isinstance(rental, Rental):
        await rental.fetch_related("updates", "bike")
    elif isinstance(rental, int):
        rental = await Rental.filter(id=rental).first().prefetch_related("updates", "bike")

    if rental.updates:
        start_time = rental.updates[0].time

        # the end time is either when the rental ended, or now.
        end_time = datetime.now()
        for update in reversed(rental.updates):
            if update.type in (RentalUpdateType.RETURN, RentalUpdateType.CANCEL):
                end_time = update.time

        location_updates = await rental.bike.location_updates.filter(time__gt=start_time, time__lt=end_time)

        if len(location_updates) > 1:
            distance = LineString(x.location for x in location_updates).length
        else:
            distance = 0
    else:
        distance = None

    return rental, distance
