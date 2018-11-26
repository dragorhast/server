"""
Defines a number of signals that the aiohttp server uses
to facilitate some of the advanced functionality.
"""

from asyncio import CancelledError
from contextlib import suppress
from datetime import timedelta

from aiohttp import WSCloseCode

from server import logger
from server.views import BikeSocketView


async def start_background_tasks(app):
    """Starts the background tasks."""
    logger.info("Starting background tasks")
    app['ticket_cleaner'] = app.loop.create_task(BikeSocketView.open_tickets.remove_all_expired(timedelta(hours=1)))


async def stop_background_tasks(app):
    """
    Stops the background tasks.

    .. note: We suppress CancelledError so that coroutines that do not handle it don't cause issues.
    """
    app['ticket_cleaner'].cancel()
    with suppress(CancelledError):
        await app['ticket_cleaner']


async def close_bike_connections(app):
    connections = set(app['bike_connections'])
    if connections:
        logger.info("Closing all open bike connections")
    for ws in set(app['bike_connections']):
        await ws.close(code=WSCloseCode.GOING_AWAY, message='Server shutdown')


def register_signals(app):
    app.on_startup.append(start_background_tasks)
    app.on_shutdown.append(close_bike_connections)
    app.on_cleanup.append(stop_background_tasks)
