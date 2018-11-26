"""
Handles the connection tickets for bikes.

The tickets are ephemeral and do not need
to be persisted.
"""

from asyncio import sleep
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Set

from server import logger
from server.models.bike import Bike


@dataclass
class BikeConnectionTicket:
    public_key: bytes
    challenge: bytes
    bike: Bike
    timestamp: datetime = field(default_factory=lambda: datetime.now())


class TooManyTicketException(Exception):
    """Raised when the store is full."""
    pass


class DuplicateTicketException(Exception):
    """
    Raised when a ticket already exists
    for that IP and public key.
    t"""


class TicketStore:
    """
    Keeps track of BikeConnectionTickets,
    limiting the number of tickets to a given
    number per IP to prevent DDoS. To execute a
    DoS, the attacker would need to send data from
    the bike, which would only take down that
    single bike.
    """

    max_tickets_per_IP = 10
    expiry_period = timedelta(minutes=1)

    issued_tickets: Dict[str, Set[BikeConnectionTicket]] = defaultdict(set)
    """A map of IP addresses and their currently issued tickets"""

    def add_ticket(self, remote, ticket: BikeConnectionTicket):
        """
        Adds a ticket to the store.
        :param remote:
        :param ticket:
        :raise TooManyTicketException: The ticket queue is full.
        :raise DuplicateTicketException: A similar ticket exists.
        """
        self.remove_expired(remote)
        tickets = self.issued_tickets[remote]

        if len(tickets) > self.max_tickets_per_IP:
            raise TooManyTicketException()
        elif any(t.public_key == ticket.public_key for t in tickets):
            raise DuplicateTicketException()
        else:
            self.issued_tickets[remote].add(ticket)

    def take_ticket(self, remote, public_key: bytes):
        """Pops the ticket with the given id, excluding expired ones."""
        match = {t for t in self.issued_tickets[remote] if t.public_key == public_key}
        if match:
            self.issued_tickets[remote] -= match
            return match.pop()
        else:
            raise KeyError("No such ticket")

    async def remove_all_expired(self, removal_period: timedelta):
        """Clears all the expired tickets."""
        while True:
            await sleep(removal_period.seconds)
            logger.debug("Clearing expired tickets")
            for remote in self.issued_tickets.keys():
                self.remove_expired(remote)

    def remove_expired(self, remote):
        """Clears expired tickets for a remote."""
        self.issued_tickets[remote] = {
            t for t in self.issued_tickets[remote]
            if t.timestamp + self.expiry_period <= datetime.now()
        }

    def __contains__(self, remote):
        """Check if a remote has any open tickets"""
        return remote in self.issued_tickets
