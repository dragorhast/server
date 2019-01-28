"""
Rentals
-------
"""

from typing import Union, Optional, Tuple, List, Dict

from server.models import Bike, Rental, RentalUpdate, User


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


async def get_rental_with_distance(target: Union[Rental, int] = None) -> Union[
    Tuple[Rental, Optional[float]], List[Tuple[Rental, float]], None]:
    """
    Gets the rentals along with their rental updates from the database. The query inner joins on location update
    and rental update, aggregating on the distance between the various location updates. This gives us our distance.
    At that point, we iterate through all the rentals with their updates, adding each update and emulating the
    "prefetch_related" functionality, since the location updates are needed in the rest of the system to get rental
    start and end.

    :param target: If supplied, limits the query to one rental.
    :returns: All the rentals with their distance and rental events included.

    ..note:: Currently only works with SQLite

    ..todo:: If any bike has no location updates, it will not be included
    ..todo:: Does not include bike
    """

    if isinstance(target, Rental):
        rental_id = target.id
    else:
        rental_id = target

    data = await Rental._meta.db.execute_query(f"""
        select R.*, RU.id 'rentalupdate_id', RU.time, RU.type, ST_Length(MakeLine(LU.location)) as 'distance'
        from rental R
            inner join locationupdate LU on LU.bike_id = R.bike_id
            inner join rentalupdate RU on R.id = RU.rental_id
        where LU.time <= (select RU.time from rentalupdate RU where RU.type IN ('return', 'cancel') and RU.rental_id = R.id)
          and LU.time >= (select RU.time from rentalupdate RU where RU.type = 'rent' and RU.rental_id = R.id)
          {("and R.id = " + str(rental_id)) if rental_id is not None else ""}
        group by R.id, RU.id
        order by LU.time;
    """)

    return_values: Dict[int, Tuple[Rental, Optional[float]]] = {}

    for row in data:
        if row["id"] not in return_values:
            rental = Rental(id=row["id"], user_id=row["user_id"], bike_id=row["bike_id"], price=row["price"])
            return_values[row["id"]] = (rental, row["distance"])
        else:
            rental, price = return_values[row["id"]]

        rental.updates._fetched = True
        rental.updates.related_objects.append(
            RentalUpdate(id=row["rentalupdate_id"], rental_id=row["id"], type=row["type"], time=row["time"]))

    if rental_id:
        try:
            return next(iter(return_values.values()))
        except StopIteration:
            # if there is no location update, return rental
            return await Rental.filter(id=rental_id).prefetch_related('updates', 'bike').first(), None
    else:
        return list(return_values.values())
