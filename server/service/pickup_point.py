from typing import Optional

from shapely.geometry import Point
from tortoise.contrib.gis.functions.comparison import Within

from server.models.pickup_point import PickupPoint


async def get_pickup_points(
    *,
    name: str = None
):
    """
    Gets the pickup points matching the given interface.

    :param name: A name to match against. Currently must match perfectly.
    """
    return await PickupPoint.all()


async def get_pickup_point(pickup_id: int):
    return await PickupPoint.get(id=pickup_id).first()


async def get_pickup_at(point: Point) -> Optional[PickupPoint]:
    return await PickupPoint.filter(Within(point, PickupPoint.area)).first()
