from server.models import User


async def create_customer(user: User, source_token: str):
    """
    Creates a new stripe customer for the given user.

    :param user: The user to create it for.
    :param source_token: The payment source to assign to the account.
    """
    pass


async def update_customer(user: User, source_token: str):
    """
    Updates the customer's payment details replacing their current payment source with the new one.

    :param user: The user to update.
    :param source_token: The new payment source to assign to the account.
    """
    pass


async def delete_customer(user: User):
    pass
