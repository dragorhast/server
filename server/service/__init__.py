"""
The service layer for the system. Acts as the internal API.
Each interface (REST API, web-sockets) should use the
service layer to implement their logic.

The service layer implements the use cases for the system.
"""

from server.service.rental_manager import InactiveRentalError, ActiveRentalError
from .ticket_store import TicketStore, TooManyTicketError, BikeConnectionTicket

MASTER_KEY = 0xdeadbeef.to_bytes(4, "big")
