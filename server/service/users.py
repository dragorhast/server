from server.models import User


async def get_users():
    return await User.all()


async def get_user(*, firebase_id=None, user_id=None) -> User:
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
