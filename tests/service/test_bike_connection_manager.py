"""
Various tests for the connection manager.

Note that since it uses weak references for its RPC and Socket caches
any usages of those objects must be saved as a variable in the test.
"""
from asyncio import TimeoutError, gather
from datetime import timedelta
from unittest.mock import PropertyMock

import pytest
from aiohttp.web_ws import WebSocketResponse
from shapely.geometry import Point

from server.models import LocationUpdate
from server.service.manager.bike_connection_manager import BikeConnectionManager, RPC


@pytest.fixture
def location_manager():
    return BikeConnectionManager()


class TestBikeConnectionManager:

    def setup_method(self):
        self._connections_closed = 0

    async def run(self):
        self._connections_closed += 1

    def conn_generator(self):
        while True:
            yield self.run()

    async def test_most_recent_location(self, location_manager, random_bike):
        """Assert that the bike always returns the most recent update."""
        await location_manager.update_location(random_bike, Point(0, 0))
        await location_manager.update_location(random_bike, Point(1, 1))
        assert location_manager.most_recent_location(random_bike)[0] == Point(1, 1)

    async def test_update_location(self, location_manager, random_bike):
        """Assert that the location update saves to the db."""
        await location_manager.update_location(random_bike, Point(0, 0))
        assert (await LocationUpdate.filter(bike=random_bike).count()) == 1
        await location_manager.update_location(random_bike, Point(1, 1))
        assert (await LocationUpdate.filter(bike=random_bike).count()) == 2

    async def test_rebuild(self, location_manager, random_bike):
        await LocationUpdate.create(bike=random_bike, location=Point(0, 0))
        await LocationUpdate.create(bike=random_bike, location=Point(1, 1))
        await location_manager.rebuild()
        assert location_manager.most_recent_location(random_bike)[0] == Point(1, 1)

    async def test_add_connection(self, location_manager, random_bike):
        """Assert that the list of connected bikes is maintained."""
        r0 = WebSocketResponse()
        await location_manager.add_connection(random_bike, r0)
        assert len(list(location_manager._bike_connections.values())) == 1

    async def test_add_connection_closes_previous(self, mocker, location_manager, random_bike):
        """Assert that adding a new socket closes the first."""

        mocked_close = mocker.patch('aiohttp.web_ws.WebSocketResponse.close')
        mocked_close.side_effect = self.conn_generator()

        r0, r1 = WebSocketResponse(), WebSocketResponse()

        await location_manager.add_connection(random_bike, r0)
        await location_manager.add_connection(random_bike, r1)

        assert mocked_close.call_count == 1

    async def test_add_connection_closed(self, mocker, location_manager, random_bike):
        """Assert that adding a closed connection fails."""

        mocked_close = mocker.patch('aiohttp.web_ws.WebSocketResponse.close')
        mocked_close.side_effect = self.conn_generator()
        mocked_closed = mocker.patch('aiohttp.web_ws.WebSocketResponse.closed')
        mocked_closed.return_value = True

        with pytest.raises(ConnectionError):
            await location_manager.add_connection(random_bike, WebSocketResponse())

    async def test_is_connected(self, location_manager, random_bike):
        """Assert that when the socket disappears, so does the bike connection."""
        r0 = WebSocketResponse()
        await location_manager.add_connection(random_bike, r0)
        location_manager._bike_locations[random_bike.id] = None
        location_manager._bike_battery[random_bike.id] = None
        location_manager._bike_locked[random_bike.id] = None
        assert location_manager.is_connected(random_bike)
        del r0
        assert not location_manager.is_connected(random_bike)

    async def test_close_connections(self, mocker, location_manager):
        """Assert that closing the connection is handled gracefully."""

        mocked_close = mocker.patch('aiohttp.web_ws.WebSocketResponse.close')
        mocked_close.side_effect = self.conn_generator()
        r0, r1 = WebSocketResponse(), WebSocketResponse()
        location_manager._bike_connections[0] = r0
        location_manager._bike_connections[1] = r1
        await location_manager.close_connections()
        assert mocked_close.call_count == 2
        assert not location_manager._bike_connections

    async def test_send_command(self, mocker, location_manager, random_bike):
        """Assert that you can send a connection to the bike using send_command."""

        async def assert_data(json):
            assert json["jsonrpc"] == "2.0"
            assert json["id"] == 1
            assert json["method"] == "test_command"
            assert "params" in json

        patched_send = mocker.patch('aiohttp.web_ws.WebSocketResponse.send_json')
        patched_send.side_effect = assert_data
        patched_counter = mocker.patch(
            'server.service.manager.bike_connection_manager.BikeConnectionManager._next_rpc_id',
        )
        patched_counter.return_value = 1

        r0 = WebSocketResponse()
        await location_manager.add_connection(random_bike, r0)

        with pytest.raises(TimeoutError):
            await location_manager._send_command(random_bike, "test_command", timeout=timedelta(seconds=0.01))

        assert patched_counter.call_count == 1

    async def test_resolve_command(self, mocker, location_manager, random_bike):
        """Assert that an opened request can be resolved."""

        async def noop(json):
            pass

        patched_send = mocker.patch('aiohttp.web_ws.WebSocketResponse.send_json')
        patched_send.side_effect = noop

        r0 = WebSocketResponse()
        rpc = RPC(1, r0, "command")
        location_manager._pending_commands[random_bike.id][1] = rpc

        rpc_request = rpc()
        rpc_resolver = location_manager.resolve_command(random_bike, 1, "returned_data")

        returned_data, _ = await gather(rpc_request, rpc_resolver)
        assert returned_data == "returned_data"
