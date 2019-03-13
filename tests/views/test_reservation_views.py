from datetime import datetime, timedelta, timezone

from server.models.reservation import ReservationOutcome
from server.serializer import JSendSchema


class TestReservationsView:

    async def test_get_all_reservations(self, client, reservation_manager, random_admin, random_pickup_point):
        reservation = await reservation_manager.reserve(
            random_admin, random_pickup_point, datetime.now(timezone.utc) + timedelta(hours=4)
        )

        response = await client.get(
            "/api/v1/reservations",
            headers={"Authorization": f"Bearer {random_admin.firebase_id}"}
        )
        response_data = JSendSchema().load(await response.json())

        assert len(response_data["data"]["reservations"]) == 1
        assert response_data["data"]["reservations"][0]["user_id"] == random_admin.id


class TestReservationView:

    async def test_get_reservation(self, client, reservation_manager, random_user, random_pickup_point):
        reservation = await reservation_manager.reserve(
            random_user, random_pickup_point, datetime.now(timezone.utc) + timedelta(hours=4)
        )

        response = await client.get(
            f"/api/v1/reservations/{reservation.id}",
            headers={"Authorization": f"Bearer {random_user.firebase_id}"}
        )
        response_data = JSendSchema().load(await response.json())
        assert response_data["data"]["reservation"]["user_id"] == random_user.id

    async def test_delete_reservation(self, client, reservation_manager, random_user, random_pickup_point):
        reservation = await reservation_manager.reserve(
            random_user, random_pickup_point, datetime.now(timezone.utc) + timedelta(hours=4)
        )

        response = await client.delete(
            f"/api/v1/reservations/{reservation.id}",
            headers={"Authorization": f"Bearer {random_user.firebase_id}"}
        )
        response_data = JSendSchema().load(await response.json())
        assert response_data["data"]["reservation"]["user_id"] == random_user.id
        assert response_data["data"]["reservation"]["status"] == ReservationOutcome.CANCELLED
