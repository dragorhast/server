"""
.. autoclasstree:: server.service

The service layer for the system. Acts as the internal API.
Each interface (REST API, web-sockets) should use the
service layer to implement their logic.

The service layer implements the use cases for the system, such
that they may be reused by anyone program that needs to access it.
It is designed to represent the business logic.
"""

from .manager.rental_manager import InactiveRentalError, ActiveRentalError, RentalManager
from .ticket_store import TicketStore, TooManyTicketError, BikeConnectionTicket

MASTER_KEY = 0xdeadbeef.to_bytes(4, "big")
