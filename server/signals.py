"""
Signals
-------

Defines a number of signals that the aiohttp server uses
to facilitate some of the advanced functionality.

Each signal must accept an the ``app`` argument.
"""
import asyncio
from asyncio import CancelledError
from contextlib import suppress
from datetime import timedelta

from aiohttp.abc import Application
from tortoise import Tortoise
from tortoise.exceptions import OperationalError

from server import logger
from server.service.rebuildable import Rebuildable
from server.service.verify_token import FirebaseVerifier
from server.views import BikeSocketView


async def close_bike_connections(app: Application):
    """Closes all outstanding connections between bikes and the server."""
    await app['bike_location_manager'].close_connections()


async def close_database_connections(app: Application):
    """Closes the open database connections."""
    await Tortoise.close_connections()


async def initialize_database(app: Application):
    """Initializes and generates the schema for our database."""
    await Tortoise.init(
        db_url=app['database_uri'],
        modules={'models': ['server.models']}
    )
    try:
        await Tortoise.generate_schemas()
    except OperationalError:
        pass


async def rebuild_event_states(app: Application):
    """Rebuilds the event-based state from the database."""
    for rebuildable in (x for x in app.values() if isinstance(x, Rebuildable)):
        await rebuildable._rebuild()


async def start_background_tasks(app: Application):
    """Starts the background tasks."""
    logger.info("Starting Background Tasks")
    loop = asyncio.get_event_loop()


    app['ticket_cleaner'] = loop.create_task(BikeSocketView.open_tickets.remove_all_expired(timedelta(hours=1)))
    loop.create_task(app['reservation_sourcer'].run())
    loop.create_task(app['statistics_reporter'].run())

    if isinstance(app['token_verifier'], FirebaseVerifier):
        loop.create_task(app['token_verifier'].get_keys(timedelta(days=1)))


async def stop_background_tasks(app):
    """
    Stops the background tasks.

    .. note: We suppress CancelledError so that coroutines that do not handle it don't cause issues.
    """
    app['ticket_cleaner'].cancel()
    with suppress(CancelledError):
        await app['ticket_cleaner']


def register_signals(app, init_database=True):
    """Registers all the signals at the appropriate hooks."""
    if init_database:
        app.on_startup.append(initialize_database)

    app.on_startup.append(rebuild_event_states)  # we deliberately rebuild the event states
    app.on_startup.append(start_background_tasks)  # before starting the background tasks

    app.on_shutdown.append(close_bike_connections)

    app.on_cleanup.append(stop_background_tasks)
    app.on_cleanup.append(close_database_connections)
