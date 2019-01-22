from server.models.pickup_point import PickupPoint


async def get_pickup_points():
    return await PickupPoint.all()


async def get_pickup_point(pickup_id: int):
    return await PickupPoint.get(id=pickup_id).first()
