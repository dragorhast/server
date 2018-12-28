from aiohttp.test_utils import TestClient

from server.serializer import UserSchema, JSendSchema


class TestUsersView:

    async def test_create_user(self, test_client: TestClient):
        """Assert that you can create a user."""

        request_schema = UserSchema()
        response_schema = JSendSchema.of(UserSchema())

    async def test_create_user_invalid_firebase(self):
        """Assert that supplying an invalid firebase key gives a descriptive error."""

    async def test_create_user_bad_schema(self):
        """Assert that creating a user with a bad schema gives a descriptive error."""


class TestUserView:

    async def test_get_user(self):
        """Assert that getting a user """

    async def test_put_user(self):
        """Assert that a user can update their entire profile."""


class TestUserRentalsView:

    async def test_get_users_rentals(self):
        """Assert that a user can get their rentals."""


class TestMeView:

    async def test_get_me(self):
        """Assert that me redirects to the appropriate user."""
