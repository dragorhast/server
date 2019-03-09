import aiohttp
import asyncio_stripe
from asyncio_stripe import Customer, Charge

from server.models import User, Rental


class CustomerError(Exception):
    pass


class DummyPaymentManager:

    def __init__(self, stripe_key=None):
        pass

    async def create_customer(self, user, source_token):
        pass

    async def is_customer(self, user):
        return True

    async def update_customer(self, user, source_token):
        pass

    async def delete_customer(self, user):
        pass

    async def charge_customer(self, user, rental, distance):
        return True, "http://www.test.com"


class PaymentManager:

    def __init__(self, stripe_key: str):
        """
        Creates a new instance of the PaymentManager class.
        """
        self._session = aiohttp.ClientSession()
        self._client = asyncio_stripe.Client(self._session, stripe_key)

    async def create_customer(self, user: User, source_token: str):
        """
        Creates a new stripe customer for the given user.

        :param user: The user to create it for.
        :param source_token: The payment source to assign to the account.
        """
        customer: Customer = await self._client.create_customer(
            email=user.email,
            description=user.first,
            source=source_token
        )

        user.stripe_id = customer.id
        await user.save()

    async def is_customer(self, user: User) -> bool:
        return user.stripe_id is not None

    async def update_customer(self, user: User, source_token: str):
        """
        Updates the customer's payment details replacing their current payment source with the new one.

        :param user: The user to update.
        :param source_token: The new payment source to assign to the account.
        """
        await self._client.update_customer(user.stripe_id, source=source_token)

    async def delete_customer(self, user: User):
        """
        Delete's the stripe customer for the given user.

        :param user: The user to delete.
        """
        await self._client.delete_customer(user.stripe_id)

        user.stripe_id = None
        await user.save()

    async def charge_customer(self, user: User, rental: Rental, distance: float = None):
        """
        Charges a given user for their rental.

        :param user: The user to charge.
        :param rental: The rental to charge for.
        :param distance: The optional distance.
        """
        distance_string = "" if distance is None else f"{distance:.2f} miles "

        charge: Charge = await self._client.create_charge(
            amount=rental.price,
            currency='gbp',
            description=f'Travelled {distance_string}on bike {rental.bike.identifier}',
            customer=user.stripe_id
        )

        return charge.status == "succeeded", charge.receipt_url
