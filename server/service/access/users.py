"""
Users
-----
"""
import os
from typing import Union, Optional, List

from tortoise.exceptions import IntegrityError

from server.models import User
from server.models.user import UserType
from server.service.firebase import FirebaseClaimManager

CLAIM_MANAGER: FirebaseClaimManager = None


class UserExistsError(Exception):
    def __init__(self, errors):
        super().__init__()
        self.errors = errors


def initialize_firebase():
    global CLAIM_MANAGER

    data = {
        "type": "service_account", "project_id": "dragorhast-420",
        "client_email": "firebase-adminsdk-ixz3j@dragorhast-420.iam.gserviceaccount.com",
        "client_id": "113526641459586902196", "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-ixz3j%40dragorhast-420.iam.gserviceaccount.com",
        "private_key_id": os.getenv("FIREBASE_KEY_ID"),
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY")
    }

    try:
        data["private_key"] = data["private_key"].replace("\\n", "\n")
    except AttributeError:
        raise RuntimeError("You must specify the Firebase private key in the environment variables.")

    CLAIM_MANAGER = FirebaseClaimManager(data)


async def get_users(*, name: str = None) -> List[User]:
    """
    Gets all the users in the system.

    :param name: An optional name to filter by.
    :return:
    """

    query = User.all()

    if name is not None:
        query = query.filter(first__icontains=name)

    return await query


async def get_user(*, firebase_id=None, user_id=None) -> Optional[User]:
    """
    :param firebase_id: The firebase id of the user to get.
    :param user_id: The user id of the user to get.
    :return: The user with the given firebase id.
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
                if "unique" in message.lower():
                    field = message.split('.')[-1]
                    errors[field] = f"User with that item already exists!"

        if not errors:
            raise error

        raise UserExistsError(errors)


async def update_user(target: Union[User, int], *, first=None, email=None):
    if isinstance(target, int):
        user = await User.get(id=target).first()
    else:
        user = target

    if first:
        user.first = first

    if email:
        user.email = email

    await user.save()
    return user


async def set_user_admin(target: Union[User, int], level: UserType) -> User:
    """Requires that the user is also registered on firebase."""
    if isinstance(target, int):
        user = await User.get(id=target).first()
    else:
        user = target

    user.type = level

    await CLAIM_MANAGER.set_user_type(user, level)

    await user.save()

    return user


async def delete_user(user: User):
    await user.delete()
