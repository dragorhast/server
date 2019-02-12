"""
Bike Connection Manager
-----------------------

The bike connection manager handles all currently connected bikes, allowing users
to send and receive information requests as well as caching the most recent location.

Responsibilities
================

This object handles everything needed for connected bikes.

- track the bike's current location
- do some reporting over which bike is where
- send messages to the bike
"""
import asyncio
from asyncio import Event
from collections import defaultdict
from datetime import datetime, timedelta
from itertools import count
from typing import Dict, Tuple, Union, Optional, List
from weakref import WeakValueDictionary

from aiohttp import WSCloseCode
from aiohttp.web_ws import WebSocketResponse
from shapely.geometry import Point, Polygon
from tortoise.query_utils import Prefetch

from server import logger
from server.models import Bike, LocationUpdate, PickupPoint
from server.models.util import resolve_id
from server.service.access.pickup_points import get_pickup_at


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
        self._bike_locations: Dict[int, Tuple[Point, datetime, Optional[PickupPoint]]] = {}
        self._bike_connections: WeakValueDictionary[int, WebSocketResponse] = WeakValueDictionary()
        self._bike_battery: Dict[int, float] = {}
        self._bike_locked: Dict[int, bool] = {}
        self._pending_commands: Dict[int, WeakValueDictionary[int, RPC]] = defaultdict(WeakValueDictionary)
        self._rpc_counter = count()

    def most_recent_location(self, target: Union[Bike, int]) -> Optional[Tuple[Point, datetime, Optional[PickupPoint]]]:
        """
        Get the most recent location of a Bike.

        :param target: The bike or its id.
        :return: The most recent location, the time it was logged, and the
        """
        bid = target.id if isinstance(target, Bike) else target
        return self._bike_locations.get(bid, None)

    def bikes_in(self, area: Union[PickupPoint, Polygon]) -> List[int]:
        """Returns the bikes that are in the given polygon."""
        return [
            bike_id for bike_id, location in self._bike_locations.items()
            if location[0].within(area.area if isinstance(area, PickupPoint) else area)
        ]

    async def update_location(
        self, target: Union[Bike, int], location: Point, time: Optional[datetime] = None
    ) -> Optional[PickupPoint]:
        """
        Updates the location of the target bike, returning the pickup point (if any) it is in.
        """
        bid = target.id if isinstance(target, Bike) else target
        time = time if time is not None else datetime.now()
        pickup = await get_pickup_at(location)
        update = await LocationUpdate.create(bike_id=bid, location=location, time=time)
        self._bike_locations[bid] = (location, time, pickup)

        if isinstance(target, Bike):
            target.updates.append(update)

        return pickup

    def update_battery(self, bike_id, percent: float):
        """Updates the battery of a given bike."""
        self._bike_battery[bike_id] = percent

    def update_locked(self, bike_id, value: bool):
        self._bike_locked[bike_id] = value

    def is_locked(self, bike_id):
        return self._bike_locked[bike_id]

    async def low_battery(self, percent: float) -> List[Bike]:
        """Gets all bikes with less than the given battery level."""
        low_battery_ids = {k: v for k, v in self._bike_battery.items() if v <= percent}
        return await Bike.filter(id__in=low_battery_ids).prefetch_related(
            Prefetch("updates", queryset=LocationUpdate.all().limit(100)))

    def battery_level(self, bike_id) -> float:
        """Gets the battery level of a given bike."""
        return self._bike_battery[bike_id]

    def is_connected(self, target: Union[Bike, int]):
        bike_id = resolve_id(target)
        return bike_id in self._bike_connections and \
               bike_id in self._bike_locked and \
               bike_id in self._bike_battery and \
               bike_id in self._bike_locations

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

    @property
    def _next_rpc_id(self):
        return next(self._rpc_counter)

    async def set_locked(self, bike_id, locked):
        await self._send_command(bike_id, "lock" if locked else "unlock")
        self._bike_locked[bike_id] = locked

    async def _send_command(self, target: Union[Bike, int], command_name: str, *args, timeout: timedelta = None):
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

    async def resolve_command(self, target: Union[Bike, int], command_id, result):
        """
        Resolves a message that the bike receives back from the server.

        This function looks up the provided RPC call in the list of pending requests
        and calls the resolve function, which awakens the response event, returning
        control (and the results) to the :func:`BikeConnectionManager.send_command`.
        """
        bike_id = resolve_id(target)
        await self._pending_commands[bike_id][command_id].resolve(result)
