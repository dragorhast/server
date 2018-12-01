from datetime import timedelta
from random import randint

import pytest
from nacl.utils import random
from pytest import raises

from server.models.bike import Bike
from server.store.ticket_store import TicketStore, BikeConnectionTicket, TooManyTicketException


@pytest.fixture
def ticket_store():
    return TicketStore()


@pytest.fixture
def random_bike() -> Bike:
    return Bike(randint(0, 100), random(32))


def test_add_ticket(ticket_store, random_bike):
    challenge = ticket_store.add_ticket("127.0.0.1", random_bike)

    assert len(ticket_store._tickets) == 1
    assert isinstance(challenge, bytes)


def test_pop_ticket(ticket_store, random_bike: Bike):
    """Make sure popped tickers function as expected."""
    challenge = ticket_store.add_ticket("127.0.0.1", random_bike)
    ticket = ticket_store.pop_ticket("127.0.0.1", random_bike.public_key)

    assert ticket
    assert isinstance(ticket, BikeConnectionTicket)
    assert ticket.remote == "127.0.0.1"
    assert ticket.challenge == challenge
    assert ticket.bike == random_bike
    assert len(ticket_store._tickets) == 0


def test_remove_expired(ticket_store, random_bike: Bike):
    """Make sure expired tickets are removed."""
    ticket_store.expiry_period = timedelta(seconds=-10)
    ticket_store.add_ticket("127.0.0.1", random_bike)

    assert ticket_store._tickets
    ticket_store.remove_expired()
    assert not ticket_store._tickets


def test_too_many_tickets(ticket_store, random_bike: Bike):
    """Make sure a remote may only add a limited number of tickets."""
    ticket_store.max_tickets_per_remote = 1
    ticket_store.add_ticket("127.0.0.1", random_bike)
    with raises(TooManyTicketException):
        ticket_store.add_ticket("127.0.0.1", random_bike)
