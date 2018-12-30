from aiohttp.test_utils import TestClient

from server.serializer import UserSchema, JSendSchema, JSendStatus


class TestUsersView:

    async def test_create_user(self, client: TestClient):
        """Assert that you can create a user."""
        request_schema = UserSchema(only=('first', 'email'))
        response_schema = JSendSchema.of(UserSchema())
        request_data = request_schema.dump({
            "first": "Alex",
            "email": "test@test.com"
        })
        response = await client.post('/api/v1/users', json=request_data, headers={
            "Authorization": "Bearer deadbeef"
        })
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert all(key in response_data["data"].keys() for key in ("first", "email"))
        assert request_data["first"] == response_data["data"]["first"]
        assert request_data["email"] == response_data["data"]["email"]
        assert response_data["data"]["firebase_id"] == bytes.fromhex("deadbeef")

    async def test_create_user_invalid_firebase(self, client: TestClient):
        """Assert that supplying an invalid firebase key gives a descriptive error."""
        request_schema = UserSchema(only=('first', 'email'))
        response_schema = JSendSchema.of(UserSchema())
        request_data = request_schema.dump({
            "first": "Alex",
            "email": "test@test.com"
        })
        response = await client.post('/api/v1/users', json=request_data)
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert all(key in response_data["data"].keys() for key in ("first", "email"))
        assert request_data["first"] == response_data["data"]["first"]
        assert request_data["email"] == response_data["data"]["email"]
        assert response_data["data"]["firebase_id"] == bytes.fromhex("deadbeef")

    async def test_create_user_bad_schema(self, client: TestClient):
        """Assert that creating a user with a bad schema gives a descriptive error."""
        response_schema = JSendSchema()
        response = await client.post('/api/v1/users', json={"bad_schema": "fail", "awful_schema": "crap"})
        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert any("Unknown field." in err for err in response_data["data"]["bad_schema"])

    async def test_create_user_duplicate(self, client: TestClient, random_user):
        """Assert that creating a user that already exists gives a descriptive error."""
        response_schema = JSendSchema()
        response = await client.post('/api/v1/users', json={
            "first": "Alex",
            "email": "test2@test.com"
        }, headers={"Authorization": f"Bearer {random_user.firebase_id}"})

        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert "firebase_id" in response_data["data"]
        assert "first" not in response_data["data"]


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
        """Assert that invalid credentials fails.."""
        response_schema = JSendSchema()
        response = await client.get(f'/api/v1/users/{random_user.id}', headers={"Authorization": f"Bearer badbad"})

        response_data = response_schema.load(await response.json())
        assert response_data["status"] == JSendStatus.FAIL
        assert any("don't have permission" in error for error in response_data["data"]["authorization"])

    async def test_put_user(self, client: TestClient, random_user):
        """Assert that an authenticated user can replace their entire profile."""
        response_schema = JSendSchema.of(UserSchema())
        request_schema = UserSchema(only=("first", "email"))
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
        pass

    async def test_put_user_malformed_data(self, client: TestClient, random_user):
        """Assert that passing an invalid user put """

    async def test_delete_user(self, client: TestClient, random_user):
        """Assert that an authenticated user can delete their profile."""


class TestUserRentalsView:

    async def test_get_users_rentals(self):
        """Assert that a user can get their rentals."""


class TestMeView:

    async def test_get_me(self, client: TestClient, random_user):
        """Assert that me redirects to the appropriate user."""
        response = await client.get('/api/v1/users/me', headers={"Authorization": f"Bearer {random_user.firebase_id}"})
        assert response.url.path == f'/api/v1/users/{random_user.id}'
