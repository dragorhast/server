import pytest

from server.models import User
from server.service.users import get_users, get_user, create_user, UserExistsError, delete_user, update_user
from tests.conftest import fake


async def test_get_users(random_user):
    assert random_user in await get_users()


async def test_get_user(random_user):
    assert random_user == await get_user(firebase_id=random_user.firebase_id, user_id=random_user.id)


async def test_create_user(database):
    user = await create_user(fake.name(), fake.email(), fake.sha1())
    users = await User.all()
    assert len(users) == 1
    assert user in users


async def test_create_user_duplicate(random_user):
    with pytest.raises(UserExistsError):
        await create_user(fake.name(), fake.email(), random_user.firebase_id)


async def test_update_user(random_user):
    name = random_user.first
    updated_random_user = await update_user(random_user, first="New Name")
    assert updated_random_user.first != name
    assert updated_random_user.first == "New Name"


async def test_delete_user(random_user):
    await delete_user(random_user)
    assert await User.all().count() == 0
