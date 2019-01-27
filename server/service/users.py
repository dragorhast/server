"""
Users
-----
"""
from typing import Union, Optional, List

from tortoise.exceptions import IntegrityError

from server.models import User


class UserExistsError(Exception):
    def __init__(self, errors):
        super().__init__()
        self.errors = errors


async def get_users() -> List[User]:
    return await User.all()


async def get_user(*, firebase_id=None, user_id=None) -> Optional[User]:
    """
    :param firebase_id: The firebase id of the user to get.
    :param user_id: The user id of the user to get.
    :return: The user with the given firebase id.
    :raises InvalidFirebaseKeyError: When the supplied firebase key is invalid.
    """

    kwargs = {}
    if firebase_id is not None:
        kwargs["firebase_id"] = firebase_id

    if user_id is not None:
        kwargs["id"] = user_id

    return await User.filter(**kwargs).first()


async def create_user(first: str, email: str, firebase_id: str) -> User:
    """
    Creates a new user.

    :param first:
    :param email:
    :param firebase_id:
    :raises UserExistsError: When the user with the given credentials already exists.
    """
    try:
        return await User.create(first=first, email=email, firebase_id=firebase_id)
    except IntegrityError as error:
        errors = {}
        for error in error.args:
            for message in error.args:
                if "UNIQUE" in message:
                    field = message.split('.')[-1]
                    errors[field] = f"User with that item already exists!"

        if not errors:
            raise error

        raise UserExistsError(errors)


async def update_user(target: Union[User, int], *, first=None, email=None):
    if isinstance(target, int):
        user = User.get(id=target).first()
    else:
        user = target

    if first:
        user.first = first

    if email:
        user.email = email

    await user.save()
    return user


async def delete_user(user: User):
    await user.delete()
