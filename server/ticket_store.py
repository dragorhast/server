"""
Handles the connection tickets for bikes.

The tickets are ephemeral and do not need
to be persisted.
"""

from asyncio import sleep
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Set

from nacl.utils import random

from server import logger
from server.models.bike import Bike


@dataclass
class BikeConnectionTicket:
    """
    Stores the challenge issued to a bike while the bike signs it.
    """

    challenge: bytes
    bike: Bike
    remote: str
    timestamp: datetime = field(default_factory=datetime.now)

    def __hash__(self):
        """Hashes the ticket based on the remote and the public key."""
        return hash((self.bike.public_key, self.remote))


class TooManyTicketException(Exception):
    """Raised when the store is full."""


class TicketStore:
    """
    Keeps track of BikeConnectionTickets,
    limiting the number of tickets to a given
    number per IP to prevent DDoS. To execute a
    DoS, the attacker would need to send data from
    the bike, which would only take down that
    single bike.

    Additionally, there can only be a single ticket
    per IP address / public key combination at any time.
    """

    _tickets: Set[BikeConnectionTicket]
    """A map of IP addresses and their currently issued tickets"""

    def __init__(self, *, max_tickets_per_remote=10, expiry_period=timedelta(seconds=10)):
        self._tickets = set()
        self.max_tickets_per_remote = max_tickets_per_remote
        self.expiry_period = expiry_period

    def add_ticket(self, remote, bike: Bike) -> bytes:
        """
        Adds a ticket to the store.

        :raise TooManyTicketException: The ticket queue is full.
        :raise DuplicateTicketException: A similar ticket exists.
        """

        tickets = {t for t in self._tickets if t.remote == remote}

        if len(tickets) >= self.max_tickets_per_remote:
            raise TooManyTicketException()

        challenge = random(64)
        ticket = BikeConnectionTicket(challenge, bike, remote)

        self._tickets.add(ticket)
        return challenge

    def pop_ticket(self, remote, public_key: bytes) -> BikeConnectionTicket:
        """Pops the ticket with the given id, excluding expired ones."""
        match = {t for t in self._tickets if t.bike.public_key == public_key and t.remote == remote}
        if not match:
            raise KeyError("No such ticket")
        self._tickets -= match
        return match.pop()

    async def remove_all_expired(self, removal_period: timedelta):
        """Clears all the expired tickets."""
        while True:
            await sleep(removal_period.seconds)
            logger.debug("Clearing expired tickets")
            self.remove_expired()

    def remove_expired(self):
        """Clears expired tickets for a remote."""
        self._tickets = {t for t in self._tickets if not self._is_expired(t)}

    def _is_expired(self, ticket):
        return ticket.timestamp + self.expiry_period <= datetime.now()

    def __contains__(self, remote):
        """Check if a remote has any open tickets"""
        return remote in self._tickets