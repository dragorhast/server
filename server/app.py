"""
App
-----
"""

import asyncio
import weakref

import sentry_sdk
import uvloop
from aiohttp import web
from aiohttp_sentry import SentryMiddleware

from server import server_mode
from server.config import api_root
from server.middleware import validate_token_middleware
from server.service.bikes import BikeLocationManager
from server.service.rental_manager import RentalManager
from server.signals import register_signals
from server.version import __version__
from server.views import register_views, send_to_developer_portal


def build_app(db_uri=None):
    """Sets up the app and installs uvloop."""
    app = web.Application(middlewares=[SentryMiddleware(), validate_token_middleware])
    uvloop.install()

    # keep a track of all open bike connections
    app['bike_connections'] = weakref.WeakSet()
    app['rental_manager'] = RentalManager()
    app['bike_location_manager'] = BikeLocationManager()
    app['database_uri'] = db_uri if db_uri is not None else 'sqlite://:memory:'

    # set up the background tasks
    register_signals(app)

    # register views
    register_views(app, api_root)
    app.router.add_get("/", send_to_developer_portal)

    # set up sentry exception tracking
    if server_mode != "development":
        sentry_sdk.init(
            dsn="https://ac31a26ce42c434e9ce1bde34768631d@sentry.io/1296249",
            environment=server_mode,
            release=f"server@{__version__}"
        )

    if server_mode == "development":
        asyncio.get_event_loop().set_debug(True)

    return app
