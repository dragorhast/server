from datetime import timedelta, datetime, timezone

from shapely.geometry import Point

from server.models import Bike, LocationUpdate, PickupPoint
from server.serializer import JSendSchema, JSendStatus
from server.serializer.fields import Many
from server.serializer.models import PickupPointSchema, BikeSchema, ReservationSchema, CreateReservationSchema
from server.service.access.pickup_points import get_pickup_points


class TestPickupsView:

    async def test_get_pickups(self, client, random_pickup_point):
        resp = await client.get('/api/v1/pickups')

        schema = JSendSchema.of(pickups=Many(PickupPointSchema()))
        data = schema.load(await resp.json())

        assert data["status"] == JSendStatus.SUCCESS

    async def test_get_bikes_in_pickup(self, client, random_pickup_point: PickupPoint):
        bike1 = await Bike.create(public_key_hex="abcdef")
        location1 = await LocationUpdate.create(bike=bike1, location=random_pickup_point.area.centroid)
        bike2 = await Bike.create(public_key_hex="badcfe")
        location2 = await LocationUpdate.create(bike=bike2, location=Point(100, 100))

        resp = await client.get(f'/api/v1/pickups/{random_pickup_point.id}/bikes')
        schema = JSendSchema.of(bikes=Many(BikeSchema()))
        data = schema.load(await resp.json())

        assert data["status"] == JSendStatus.SUCCESS
        assert len(data["data"]["bikes"]) == 1
        assert data["data"]["bikes"][0]["public_key"] == b'\xab\xcd\xef'


class TestPickupView:

    async def test_get_pickup(self, client, random_pickup_point):
        resp = await client.get(f'/api/v1/pickups/{random_pickup_point.id}')
        resp_data = await resp.json()
        assert resp_data["data"]["pickup"]["properties"]["name"] == random_pickup_point.name

    async def test_delete_pickup(self, client, random_pickup_point, random_admin):
        resp = await client.delete(
            f'/api/v1/pickups/{random_pickup_point.id}',
            headers={"Authorization": f"Bearer {random_admin.firebase_id}"}
        )

        assert resp.status == 204
        assert len(await get_pickup_points()) == 0


class TestPickupReservationsView:

    async def test_get_pickup_reservations(self, client, random_pickup_point, reservation_manager, random_admin):
        await reservation_manager.reserve(random_admin, random_pickup_point, datetime.now(timezone.utc) + timedelta(hours=4))
        resp = await client.get(
            f'/api/v1/pickups/{random_pickup_point.id}/reservations',
            headers={"Authorization": f"Bearer {random_admin.firebase_id}"}
        )
        response_data = JSendSchema.of(reservations=Many(ReservationSchema())).load(await resp.json())
        assert len(response_data["data"]["reservations"]) == 1

    async def test_create_pickup_reservation(self, client, random_pickup_point, reservation_manager, random_user):

        request_data = CreateReservationSchema().dump({
            "reserved_for": datetime.now() + timedelta(hours=4)
        })

        response = await client.post(
            f"/api/v1/pickups/{random_pickup_point.id}/reservations",
            headers={"Authorization": f"Bearer {random_user.firebase_id}"},
            json=request_data
        )

        response_data = JSendSchema.of(reservation=ReservationSchema()).load(await response.json())
        assert response_data["data"]["reservation"]["user_id"] == random_user.id
