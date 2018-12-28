from typing import Union

from server.models import Bike, Rental


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

    return await Rental.filter(bike__id=bid)


async def get_rentals():
    return await Rental.all()
