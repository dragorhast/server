from server.models import User


async def get_users():
    return await User.all()


async def get_user(firebase_id) -> User:
    """
    :param firebase_id: The firebase id of the user to get.
    :return: The user with the given firebase id.
    :raises InvalidFirebaseKeyError: When the supplied firebase key is invalid.
    """
    return await User.filter(firebase_id=firebase_id).first()