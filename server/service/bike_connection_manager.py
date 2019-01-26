"""
Bike Connection Manager
-----------------------

The bike connection manager handles all currently connected bikes, allowing users
to send and receive information requests as well as caching the most recent location.
"""
import asyncio
from asyncio import Event
from collections import defaultdict
from datetime import datetime, timedelta
from itertools import count
from typing import Dict, Tuple, Union, Optional
from weakref import WeakValueDictionary

import dateparser
from aiohttp import WSCloseCode
from aiohttp.web_ws import WebSocketResponse
from shapely.geometry import Point
from shapely.wkt import loads

from server import logger
from server.models import Bike, LocationUpdate
from server.models.util import resolve_id


class RPC:

    def __init__(self, rpc_id, socket: WebSocketResponse, command_name: str, args: list = None):
        self.id = rpc_id
        self.command_name = command_name
        self.args = args if args is not None else []
        self.return_data = None

        self._response_event = Event()
        self._resolved = False
        self._socket = socket

    async def __call__(self):
        """This function calls the RPC, sending the json to the bike, and waits for the response event."""
        await self._socket.send_json({
            "jsonrpc": "2.0",
            "id": self.id,
            "method": self.command_name,
            "params": self.args,
        })
        await self._response_event.wait()
        return self.return_data

    async def resolve(self, return_data):
        """Resolves the RPC, setting its return data and giving control back to the caller."""
        if self._resolved:
            raise ValueError("This RPC has already been resolved.")

        self._resolved = True
        self.return_data = return_data
        self._response_event.set()


class BikeConnectionManager:
    """
    Maintains bike location state, and facilitates querying data on connected bikes.
    You may call functions on a bike by awaiting :func:`BikeConnectionManager.send_command`.

    The RPC objects and sockets in this manager are all weak references, meaning their
    references will be removed automatically when all references to them are lost.
    """

    def __init__(self):
        self._bike_locations: Dict[int, Tuple[Point, datetime]] = {}
        self._bike_connections: WeakValueDictionary[int, WebSocketResponse] = WeakValueDictionary()
        self._pending_commands: Dict[int, WeakValueDictionary[int, RPC]] = defaultdict(WeakValueDictionary)
        self._rpc_counter = count()

    def most_recent_location(self, target: Union[Bike, int]) -> Tuple[Point, datetime]:
        bid = target.id if isinstance(target, Bike) else target
        return self._bike_locations[bid]

    async def update_location(self, target: Union[Bike, int], location: Point, time: Optional[datetime] = None):
        bid = target.id if isinstance(target, Bike) else target
        time = time if time is not None else datetime.now()
        await LocationUpdate.create(bike_id=bid, location=location, time=time)
        self._bike_locations[bid] = (location, time)

    def is_connected(self, target: Union[Bike, int]):
        bike_id = resolve_id(target)
        return bike_id in self._bike_connections

    async def add_connection(self, target: Union[Bike, int], socket: WebSocketResponse):
        if socket.closed:
            raise ConnectionError("New socket is closed.")

        bike_id = resolve_id(target)
        if bike_id in self._bike_connections:
            await self._bike_connections[bike_id].close()
        self._bike_connections[bike_id] = socket

    async def close_connections(self):
        if self._bike_connections:
            logger.info("Closing all open bike connections")
        for connection in self._bike_connections.values():
            await connection.close(code=WSCloseCode.GOING_AWAY)
        self._bike_connections = {}

    async def rebuild(self):
        """
        Rebuilds the bike location state from the database.

        ..note:: Currently only works with SQLite
        """
        recent_updates = await LocationUpdate._meta.db.execute_query(
            "select U.bike_id, max(U.time) as 'time', ST_AsText(U.location) as 'location' "
            "from locationupdate U group by U.bike_id"
        )
        for update in recent_updates:
            self._bike_locations[update["bike_id"]] = (
                loads(update["location"]),
                dateparser.parse(update["time"])
            )

    @property
    def _next_rpc_id(self):
        return next(self._rpc_counter)

    async def send_command(self, target: Union[Bike, int], command_name: str, *args, timeout: timedelta = None):
        """
        Sends a command to a bike, and blocks until it receives a response.

        :raises ConnectionError: When there is no active connection to the bike.
        :raises TimeoutError: When the call times out before the given delta.
        """
        bike_id = resolve_id(target)
        connection = self._bike_connections[bike_id]
        rpc = RPC(self._next_rpc_id, connection, command_name, args)
        self._pending_commands[bike_id][rpc.id] = rpc
        return await asyncio.wait_for(rpc(), timeout=timeout.total_seconds() if timeout is not None else None)

    async def resolve_command(self, target: Union[Bike, int], command_id, arguments):
        """
        Resolves a message that the bike receives back from the server.

        This function looks up the provided RPC call in the list of pending requests
        and calls the resolve function, which awakens the response event, returning
        control (and the results) to the :func:`BikeConnectionManager.send_command`.
        """
        bike_id = resolve_id(target)
        await self._pending_commands[bike_id][command_id].resolve(arguments)
