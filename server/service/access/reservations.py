"""
Reservations
============
"""

from datetime import datetime
from typing import List, Union, Optional

from server.models import Reservation, PickupPoint, User


async def get_reservations(*ids) -> List[Reservation]:
    """Gets all the reservations matching the given ids."""
    if ids:
        query = Reservation.filter(id__in=ids)
    else:
        query = Reservation.all()

    return await query.prefetch_related("pickup_point", "user")


async def get_reservation(rid) -> Optional[Reservation]:
    """Gets the reservation with the given id."""
    reservations = await get_reservations(rid)
    if reservations:
        return reservations[0]
    return None


async def current_reservation(user: Union[User, int]) -> Optional[Reservation]:
    """
    Gets the current reservation for a given user or user id.

    The current reservation is one that isn't claimed, and that
    is reserved for the future.
    """
    kwargs = {
        "outcome__isnull": True
    }

    if isinstance(user, User):
        kwargs["user"] = user
    else:
        kwargs["user_id"] = user

    return await Reservation.filter(**kwargs).first().prefetch_related("pickup_point", "user")


async def get_user_reservations(user: Union[User, int]):
    uid = user.id if isinstance(user, User) else user
    return await Reservation.filter(user_id=uid).prefetch_related("pickup_point", "user")


async def create_reservation(user: User, pickup_point: PickupPoint, reserved_for: datetime) -> Reservation:
    reservation = await Reservation.create(user=user, pickup_point=pickup_point, reserved_for=reserved_for)
    reservation.pickup_point = pickup_point
    reservation.user = user
    return reservation
