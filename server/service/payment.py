import abc
import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial
from typing import Optional

import aiohttp
import stripe

from server.models import User, Rental


class CustomerError(Exception):
    pass


class PaymentManager(abc.ABC):
    @abc.abstractmethod
    async def create_customer(self, user, source_token):
        pass

    @abc.abstractmethod
    async def is_customer(self, user):
        return True

    @abc.abstractmethod
    async def update_customer(self, user, source_token):
        pass

    @abc.abstractmethod
    async def delete_customer(self, user):
        pass

    @abc.abstractmethod
    async def charge_customer(self, user, rental, distance) -> (bool, Optional[str]):
        pass


class DummyPaymentManager(PaymentManager):

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
        return True, None


class PaymentManager(PaymentManager):

    def __init__(self, stripe_key: str):
        """
        Creates a new instance of the PaymentManager class.
        """
        stripe.api_key = stripe_key
        self._session = aiohttp.ClientSession()

        self._loop = asyncio.get_event_loop()
        self._executor = ThreadPoolExecutor()

    async def _run_in_executor(self, func, *args, **kwargs):
        pfunc = partial(func, *args, **kwargs)
        return await self._loop.run_in_executor(
            self._executor,
            pfunc
        )

    async def create_customer(self, user: User, source_token: str):
        """
        Creates a new stripe customer for the given user.

        :param user: The user to create it for.
        :param source_token: The payment source to assign to the account.
        """

        customer = await self._run_in_executor(
            stripe.Customer.create,
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
        await self._run_in_executor(
            stripe.Customer.modify,
            user.stripe_id,
            source=source_token,
        )

    async def delete_customer(self, user: User):
        """
        Delete's the stripe customer for the given user.

        :param user: The user to delete.
        """
        await self._run_in_executor(
            stripe.Customer.delete,
            user.stripe_id
        )

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

        charge = await self._run_in_executor(
            stripe.Charge.create,
            amount=rental.price,
            currency='gbp',
            description=f'Travelled {distance_string}on bike {rental.bike.identifier}',
            customer=user.stripe_id
        )

        return charge.status == "succeeded", charge.receipt_url
