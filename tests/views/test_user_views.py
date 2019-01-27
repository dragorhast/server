from aiohttp.test_utils import TestClient

from server.models import User
from server.serializer import UserSchema, JSendSchema, JSendStatus, RentalSchema


class TestUsersView:

    async def test_get_users(self, client: TestClient, random_admin: User):
        """Assert that you can get a list of users."""
        response_schema = JSendSchema.of(UserSchema(many=True))
        response = await client.get('/api/v1/users', headers={"Authorization": f"Bearer {random_admin.firebase_id}"})
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert any(user["id"] == random_admin.id for user in response_data["data"])

    async def test_create_user(self, client: TestClient):
        """Assert that you can create a user."""
        request_schema = UserSchema(only=('first', 'email'))
        response_schema = JSendSchema.of(UserSchema())
        request_data = request_schema.dump({
            "first": "Alex",
            "email": "test@test.com"
        })
        response = await client.post('/api/v1/users', json=request_data, headers={"Authorization": "Bearer deadbeef"})
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert all(key in response_data["data"].keys() for key in ("first", "email"))
        assert request_data["first"] == response_data["data"]["first"]
        assert request_data["email"] == response_data["data"]["email"]
        assert response_data["data"]["firebase_id"] == bytes.fromhex("deadbeef")

    async def test_create_user_invalid_firebase(self, client: TestClient):
        """Assert that supplying an invalid firebase key gives a descriptive error."""
        request_schema = UserSchema(only=('first', 'email'))
        response_schema = JSendSchema()
        request_data = request_schema.dump({
            "first": "Alex",
            "email": "test@test.com"
        })
        response = await client.post('/api/v1/users', json=request_data, headers={"Authorization": "Bearer invalid"})
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert any("Not a valid hex string" in error for error in response_data["data"]["errors"])

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

    async def test_create_user_duplicate(self, client: TestClient, random_user):
        """Assert that creating a user that already exists just updates the user."""
        response_schema = JSendSchema()
        response = await client.post('/api/v1/users', json={
            "first": "Alex",
            "email": "test2@test.com"
        }, headers={"Authorization": f"Bearer {random_user.firebase_id}"})

        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert "firebase_id" in response_data["data"]
        assert "first" in response_data["data"]


class TestUserView:

    async def test_get_user(self, client: TestClient, random_user):
        """Assert that an authenticated user can get their profile."""
        response_schema = JSendSchema.of(UserSchema())
        response = await client.get(f'/api/v1/users/{random_user.id}',
                                    headers={"Authorization": f"Bearer {random_user.firebase_id}"})

        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert response_data["data"]["first"] == random_user.first

    async def test_get_user_bad_credentials(self, client, random_user):
        """Assert that providing invalid credentials fails."""
        response_schema = JSendSchema()
        response = await client.get(f'/api/v1/users/{random_user.id}', headers={"Authorization": f"Bearer badbad"})

        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert any("doesn't exist" in error for error in response_data["data"]["authorization"])

    async def test_get_user_as_admin(self, client, random_user, random_admin):
        """Assert that getting any user's credentials as an admin works."""
        response_schema = JSendSchema()
        response = await client.get(f'/api/v1/users/{random_user.id}',
                                    headers={"Authorization": f"Bearer {random_admin.firebase_id}"})

        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert response_data["data"]["first"] == random_user.first

    async def test_put_user(self, client: TestClient, random_user):
        """Assert that an authenticated user can replace their entire profile."""
        request_schema = UserSchema(only=("first", "email"))
        response_schema = JSendSchema.of(UserSchema())

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
        assert response_data["data"]["first"] == random_user.first + " Jones"

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
        response_schema = JSendSchema.of(RentalSchema(many=True))
        response = await client.get(
            f'/api/v1/users/{random_user.id}/rentals',
            headers={"Authorization": f"Bearer {random_user.firebase_id}"}
        )
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert isinstance(response_data["data"], list)


class TestUserCurrentRentalView:

    async def test_get_current_rental(self, client: TestClient, random_user, random_bike):
        """Assert that a user can get their current rental."""
        rental = await client.app["rental_manager"].create(random_user, random_bike)

        response_schema = JSendSchema.of(RentalSchema())
        response = await client.get(
            '/api/v1/users/me/rentals/current',
            headers={"Authorization": f"Bearer {random_user.firebase_id}"}
        )

        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert response_data["data"]["id"] == rental.id
        assert "price" not in response_data["data"]
        assert "estimated_price" in response_data["data"]
        assert response_data["data"]["bike_id"] == random_bike.id
        assert response_data["data"]["user_id"] == random_user.id
        assert "start_time" in response_data["data"]

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

    async def test_end_current_rental(self, client: TestClient, random_user, random_bike, rental_manager):
        """Assert that a user can end their rental by performing a DELETE"""
        rental = await client.app["rental_manager"].create(random_user, random_bike)
        response_schema = JSendSchema.of(RentalSchema())
        response = await client.delete(
            '/api/v1/users/me/rentals/current',
            headers={"Authorization": f"Bearer {random_user.firebase_id}"}
        )
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert response_data["data"]["id"] == rental.id
        assert response_data["data"]["bike_id"] == random_bike.id
        assert response_data["data"]["user_id"] == random_user.id
        assert "start_time" in response_data["data"]
        assert "end_time" in response_data["data"]
        assert "price" in response_data["data"]

    async def test_end_current_rental_none(self, client: TestClient, random_user):
        """Assert that the user is warned when trying to end a rental when there is none."""
        response_schema = JSendSchema()
        response = await client.delete(
            '/api/v1/users/me/rentals/current',
            headers={"Authorization": f"Bearer {random_user.firebase_id}"}
        )
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert response_data["data"]["message"] == "You have no current rental."


class TestMeView:

    async def test_get_me(self, client: TestClient, random_user):
        """Assert that me redirects to the appropriate user."""
        response = await client.get('/api/v1/users/me', headers={"Authorization": f"Bearer {random_user.firebase_id}"})
        assert response.url.path == f'/api/v1/users/{random_user.id}'

    async def test_get_me_missing_auth(self, client: TestClient, random_user):
        """Assert that not supplying a valid token errors."""
        response = await client.get('/api/v1/users/me')
        response_schema = JSendSchema()
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert "authorization" in response_data["data"]
        assert any("supply your firebase token" in error for error in response_data["data"]["authorization"])

    async def test_get_me_invalid_auth(self, client: TestClient, random_user):
        """Assert that an invalid token returns an appropriate error."""
        response = await client.get('/api/v1/users/me', headers={"Authorization": "Bearer bad_token"})
        response_schema = JSendSchema()
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert any("valid hex string" in error for error in response_data["data"]["errors"])

    async def test_get_me_missing_user(self, client: TestClient):
        """Assert that calling me gives a descriptive error."""
        response = await client.get('/api/v1/users/me', headers={"Authorization": "Bearer abcd"})
        response_schema = JSendSchema()
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        print(response_data)
        assert "User does not exist" in response_data["data"]["message"]
