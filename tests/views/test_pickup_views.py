from shapely.geometry import Point

from server.models import Bike, LocationUpdate, PickupPoint
from server.serializer import JSendSchema, JSendStatus
from server.serializer.models import PickupPointSchema, BikeSchema


class TestPickupsView:

    async def test_get_pickups(self, client, random_pickup_point):
        resp = await client.get('/api/v1/pickups')

        schema = JSendSchema.of(PickupPointSchema(many=True))
        data = schema.load(await resp.json())

        assert data["status"] == JSendStatus.SUCCESS

    async def test_get_bikes_in_pickup(self, client, random_pickup_point: PickupPoint):
        bike1 = await Bike.create(public_key_hex="abcdef")
        location1 = await LocationUpdate.create(bike=bike1, location=random_pickup_point.area.centroid)
        bike2 = await Bike.create(public_key_hex="badcfe")
        location2 = await LocationUpdate.create(bike=bike2, location=Point(100, 100))

        resp = await client.get(f'/api/v1/pickups/{random_pickup_point.id}/bikes')
        schema = JSendSchema.of(BikeSchema(many=True))
        data = schema.load(await resp.json())

        assert data["status"] == JSendStatus.SUCCESS
        assert len(data["data"]) == 1
        assert data["data"][0]["public_key"] == b'\xab\xcd\xef'