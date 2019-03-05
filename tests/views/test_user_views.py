from datetime import timezone, datetime, timedelta

from aiohttp.test_utils import TestClient
from marshmallow.fields import String, Url
from shapely.geometry import Point

from server.models import User
from server.serializer import JSendSchema, JSendStatus
from server.serializer.fields import Many
from server.serializer.models import IssueSchema, UserSchema, RentalSchema, CurrentRentalSchema, ReservationSchema, \
    CurrentReservationSchema
from server.service.access.issues import open_issue


class TestUsersView:

    async def test_get_users(self, client: TestClient, random_admin: User):
        """Assert that you can get a list of users."""
        response_schema = JSendSchema.of(users=Many(UserSchema()))
        response = await client.get('/api/v1/users', headers={"Authorization": f"Bearer {random_admin.firebase_id}"})
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert any(user["id"] == random_admin.id for user in response_data["data"]["users"])

    async def test_create_user(self, client: TestClient):
        """Assert that you can create a user."""
        request_schema = UserSchema(only=('first', 'email'))
        response_schema = JSendSchema.of(user=UserSchema())
        request_data = request_schema.dump({
            "first": "Alex",
            "email": "test@test.com"
        })
        response = await client.post('/api/v1/users', json=request_data, headers={"Authorization": "Bearer deadbeef"})
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert all(key in response_data["data"]["user"].keys() for key in ("first", "email"))
        assert request_data["first"] == response_data["data"]["user"]["first"]
        assert request_data["email"] == response_data["data"]["user"]["email"]
        assert response_data["data"]["user"]["firebase_id"] == "deadbeef"

    async def test_create_user_invalid_firebase(self, client: TestClient):
        """Assert that supplying an invalid firebase key gives a descriptive error."""
        request_schema = UserSchema(only=('first', 'email'))
        response_schema = JSendSchema()
        request_data = request_schema.dump({
            "first": "Alex",
            "email": "test@test.com"
        })
        response = await client.post('/api/v1/users', json=request_data, headers={"Authorization": "Bearer "})
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert any("Invalid" == error for error in response_data["data"]["errors"])

    async def test_create_user_bad_schema(self, client: TestClient):
        """Assert that creating a user with a bad schema gives a descriptive error."""
        response_schema = JSendSchema()
        response = await client.post(
            '/api/v1/users',
            json={"bad_schema": "fail", "awful_schema": "crap"},
            headers={"Authorization": "Bearer deadbeef"}
        )
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert any("Unknown field." in err for err in response_data["data"]["errors"]["bad_schema"])


class TestUserView:

    async def test_get_user(self, client: TestClient, random_user):
        """Assert that an authenticated user can get their profile."""
        response_schema = JSendSchema.of(user=UserSchema())
        response = await client.get(f'/api/v1/users/{random_user.id}',
                                    headers={"Authorization": f"Bearer {random_user.firebase_id}"})

        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert response_data["data"]["user"]["first"] == random_user.first

    async def test_get_user_bad_credentials(self, client, random_user):
        """Assert that providing invalid credentials fails."""
        response_schema = JSendSchema()
        response = await client.get(f'/api/v1/users/{random_user.id}', headers={"Authorization": f"Bearer badbad"})

        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert any("doesn't have access" in error for error in response_data["data"]["reasons"])

    async def test_get_user_as_admin(self, client, random_user, random_admin):
        """Assert that getting any user's credentials as an admin works."""
        response_schema = JSendSchema()
        response = await client.get(f'/api/v1/users/{random_user.id}',
                                    headers={"Authorization": f"Bearer {random_admin.firebase_id}"})

        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert response_data["data"]["user"]["first"] == random_user.first

    async def test_put_user(self, client: TestClient, random_user):
        """Assert that an authenticated user can replace their entire profile."""
        request_schema = UserSchema(only=("first", "email"))
        response_schema = JSendSchema.of(user=UserSchema())

        request_data = request_schema.load({
            "first": random_user.first + " Jones",
            "email": "new_" + random_user.email
        })
        response = await client.put(
            f'/api/v1/users/{random_user.id}',
            json=request_data,
            headers={"Authorization": f"Bearer {random_user.firebase_id}"},
        )

        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert response_data["data"]["user"]["first"] == random_user.first + " Jones"

    async def test_put_user_malformed_data(self, client: TestClient, random_user):
        """Assert that passing malformed data to the put fails."""
        response_schema = JSendSchema()
        response = await client.put(
            f'/api/v1/users/{random_user.id}',
            json={"first": 12345},
            headers={"Authorization": f"Bearer {random_user.firebase_id}"},
        )
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL

    async def test_delete_user(self, client: TestClient, random_user):
        """Assert that an authenticated user can delete their profile."""
        response = await client.delete(f'/api/v1/users/{random_user.id}',
                                       headers={"Authorization": f"Bearer {random_user.firebase_id}"})
        assert response.status == 204
        assert await User.all().count() == 0

    async def test_delete_user_as_admin(self, client, random_user, random_admin):
        """Assert that an admin can delete any user's account."""
        response = await client.delete(f'/api/v1/users/{random_user.id}',
                                       headers={"Authorization": f"Bearer {random_admin.firebase_id}"})
        assert response.status == 204
        assert await User.all().count() == 1


class TestUserRentalsView:

    async def test_get_users_rentals(self, client: TestClient, random_user):
        """Assert that a user can get their rentals."""
        response_schema = JSendSchema.of(rentals=Many(RentalSchema()))
        response = await client.get(
            f'/api/v1/users/{random_user.id}/rentals',
            headers={"Authorization": f"Bearer {random_user.firebase_id}"}
        )
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert isinstance(response_data["data"]["rentals"], list)


class TestUserCurrentRentalView:

    async def test_get_current_rental(self, client: TestClient, random_user, random_bike):
        """Assert that a user can get their current rental."""
        rental, location = await client.app["rental_manager"].create(random_user, random_bike)

        response_schema = JSendSchema.of(rental=CurrentRentalSchema())
        response = await client.get(
            '/api/v1/users/me/rentals/current',
            headers={"Authorization": f"Bearer {random_user.firebase_id}"}
        )

        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert response_data["data"]["rental"]["id"] == rental.id
        assert "price" not in response_data["data"]["rental"]
        assert "estimated_price" in response_data["data"]["rental"]
        assert response_data["data"]["rental"]["bike_identifier"] == random_bike.identifier
        assert response_data["data"]["rental"]["user_id"] == random_user.id
        assert "start_time" in response_data["data"]["rental"]

    async def test_get_current_rental_none(self, client: TestClient, random_user):
        """Assert that a user is warned when they have no current rental."""
        response_schema = JSendSchema()
        response = await client.get(
            '/api/v1/users/me/rentals/current',
            headers={"Authorization": f"Bearer {random_user.firebase_id}"}
        )

        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert response_data["data"]["message"] == "You have no current rental."

    async def test_end_current_rental(self, client: TestClient, random_user, random_bike, rental_manager, bike_connection_manager):
        """Assert that a user can end their rental."""
        rental, location = await rental_manager.create(random_user, random_bike)
        await bike_connection_manager.update_location(random_bike, Point(100, 0))

        response_schema = JSendSchema.of(rental=RentalSchema(), action=String(), receipt_url=Url())
        response = await client.patch(
            '/api/v1/users/me/rentals/current/complete',
            headers={"Authorization": f"Bearer {random_user.firebase_id}"}
        )

        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert response_data["data"]["rental"]["id"] == rental.id
        assert response_data["data"]["rental"]["bike_identifier"] == random_bike.identifier
        assert response_data["data"]["rental"]["user_id"] == random_user.id
        assert "start_time" in response_data["data"]["rental"]
        assert "end_time" in response_data["data"]["rental"]
        assert "price" in response_data["data"]["rental"]
        assert response_data["data"]["action"] == "completed"

    async def test_cancel_current_rental(self, client: TestClient, random_user, random_bike, rental_manager):
        """Assert that a user can cancel their rental."""
        rental, location = await rental_manager.create(random_user, random_bike)
        response_schema = JSendSchema.of(rental=RentalSchema(), action=String(), receipt_url=Url(allow_none=True))
        response = await client.patch(
            '/api/v1/users/me/rentals/current/cancel',
            headers={"Authorization": f"Bearer {random_user.firebase_id}"}
        )

        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert response_data["data"]["rental"]["id"] == rental.id
        assert response_data["data"]["rental"]["bike_identifier"] == random_bike.identifier
        assert response_data["data"]["rental"]["user_id"] == random_user.id
        assert "start_time" in response_data["data"]["rental"]
        assert "cancel_time" in response_data["data"]["rental"]
        assert response_data["data"]["action"] == "canceled"

    async def test_end_current_rental_none(self, client: TestClient, random_user):
        """Assert that the user is warned when trying to end a rental when there is none."""
        response_schema = JSendSchema()
        response = await client.patch(
            '/api/v1/users/me/rentals/current/complete',
            headers={"Authorization": f"Bearer {random_user.firebase_id}"}
        )
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert response_data["data"]["message"] == "You have no current rental."


class TestUserIssuesView:

    async def test_get_user_issues(self, client, random_user):
        """Assert that the system can retrieve the issues for a user."""
        created_issue = await open_issue(random_user, "Uh oh!")
        response = await client.get("/api/v1/users/me/issues",
                                    headers={"Authorization": f"Bearer {random_user.firebase_id}"})
        response_data = JSendSchema.of(issues=Many(IssueSchema())).load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert isinstance(response_data["data"]["issues"], list)
        assert any(created_issue.id == issue["id"] for issue in response_data["data"]["issues"])

    async def test_add_user_issue(self, client, random_user):
        """Assert that a user can create an issue."""
        response = await client.post(
            "/api/v1/users/me/issues",
            headers={"Authorization": f"Bearer {random_user.firebase_id}"},
            json={"description": "I'm not happy!"}
        )

        response_data = JSendSchema.of(issue=IssueSchema()).load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert response_data["data"]["issue"]["description"] == "I'm not happy!"

    async def test_add_user_bike_issue(self, client, random_user, random_bike):
        """Assert that a user can create an issue for a bike."""
        response = await client.post(
            "/api/v1/users/me/issues",
            headers={"Authorization": f"Bearer {random_user.firebase_id}"},
            json={"description": "I'm not happy!", "bike_identifier": random_bike.identifier}
        )

        response_data = JSendSchema.of(issue=IssueSchema()).load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert response_data["data"]["issue"]["description"] == "I'm not happy!"
        assert response_data["data"]["issue"]["bike_identifier"] == random_bike.identifier


class TestUserReservationsView:

    async def test_get_users_reservations(self, client, random_user, reservation_manager, random_pickup_point):
        """Assert that a user or admin can get the reservations for a user."""
        reservation = await reservation_manager.reserve(random_user, random_pickup_point,
                                                        datetime.now(timezone.utc) + timedelta(hours=4))
        response = await client.get(
            "/api/v1/users/me/reservations",
            headers={"Authorization": f"Bearer {random_user.firebase_id}"}
        )

        response_data = JSendSchema.of(reservations=Many(ReservationSchema())).load(await response.json())
        assert len(response_data["data"]["reservations"]) == 1


class TestUserCurrentReservationView:

    async def test_get_users_current_reservations(self, client, random_user, reservation_manager, random_pickup_point):
        """Assert that a user can get their current reservation."""
        await reservation_manager.reserve(random_user, random_pickup_point,
                                          datetime.now(timezone.utc) + timedelta(hours=4))
        response = await client.get(
            "/api/v1/users/me/reservations/current",
            headers={"Authorization": f"Bearer {random_user.firebase_id}"}
        )

        response_data = JSendSchema.of(reservations=Many(CurrentReservationSchema())).load(await response.json())
        assert response_data["data"]["reservations"][0]["user_id"] == random_user.id
        assert "url" in response_data["data"]["reservations"][0]


class TestMeView:

    async def test_get_me(self, client: TestClient, random_user):
        """Assert that me redirects to the appropriate user."""
        response = await client.get('/api/v1/users/me',
                                    headers={"Authorization": f"Bearer {random_user.firebase_id}"})
        assert response.url.path == f'/api/v1/users/{random_user.id}'
        response_data = JSendSchema.of(user=UserSchema()).load(await response.json())
        assert response_data["data"]["user"]["first"] == random_user.first
        assert response_data["data"]["user"]["email"] == random_user.email

    async def test_get_me_missing_auth(self, client: TestClient, random_user):
        """Assert that not supplying a valid token errors."""
        response = await client.get('/api/v1/users/me')
        response_schema = JSendSchema()
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert "reasons" in response_data["data"]
        assert any("Authorization header was not included" in error for error in response_data["data"]["reasons"])

    async def test_get_me_invalid_auth(self, client: TestClient, random_user):
        """Assert that an invalid token returns an appropriate error."""
        response = await client.get('/api/v1/users/me', headers={"Authorization": "Bearer "})
        response_schema = JSendSchema()
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert any("Invalid" == error for error in response_data["data"]["errors"])

    async def test_get_me_missing_user(self, client: TestClient):
        """Assert that calling me gives a descriptive error."""
        response = await client.get('/api/v1/users/me', headers={"Authorization": "Bearer abcd"})
        response_schema = JSendSchema()
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        print(response_data)
        assert "User does not exist" in response_data["data"]["message"]
