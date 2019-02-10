"""
App
-----
"""

import asyncio

import sentry_sdk
import uvloop
from aiohttp import web
from aiohttp_apispec import setup_aiohttp_apispec
from aiohttp_sentry import SentryMiddleware

from server import server_mode, logger
from server.config import api_root
from server.middleware import validate_token_middleware
from server.service.manager.bike_connection_manager import BikeConnectionManager
from server.service.manager.rental_manager import RentalManager
from server.service.manager.reservation_manager import ReservationManager
from server.service.verify_token import FirebaseVerifier, DummyVerifier
from server.signals import register_signals
from server.version import __version__, name
from server.views import register_views, redoc, logo


def build_app(db_uri=None):
    """Sets up the app and installs uvloop."""
    app = web.Application(middlewares=[SentryMiddleware(), validate_token_middleware])
    uvloop.install()

    # keep a track of all open bike connections
    app['bike_location_manager'] = BikeConnectionManager()
    app['rental_manager'] = RentalManager()
    app['reservation_manager'] = ReservationManager(app['bike_location_manager'], app['rental_manager'])
    app['database_uri'] = db_uri if db_uri is not None else 'spatialite://:memory:'

    if server_mode == "development":
        verifier = DummyVerifier()
    else:
        verifier = FirebaseVerifier("dragorhast-420")

    app['token_verifier'] = verifier

    # set up the background tasks
    register_signals(app)

    # register views
    register_views(app, api_root)
    app.router.add_get("/", redoc)
    app.router.add_get("/logo.svg", logo)

    setup_aiohttp_apispec(
        app=app, title=name, version=__version__, url=f"{api_root}/docs",
        servers=[{"url": "http://api.tap2go.co.uk"}],
        info={"x-logo": {
            "url": "/logo.svg",
            "altText": "tap2go logo"
        }},
        externalDocs={
            "description": "Tap2Go Software Docs",
            "url": "https://tap2go-server.netlify.com/"
        },
        components={
            "securitySchemes": {
                "FirebaseToken": {
                    "type": "http",
                    "description": "A valid firebase token JWT",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            }
        },
    )

    # set up sentry exception tracking
    if server_mode != "development":
        logger.info("Starting Sentry Logging")
        sentry_sdk.init(
            dsn="https://ac31a26ce42c434e9ce1bde34768631d@sentry.io/1296249",
            environment=server_mode,
            release=f"server@{__version__}"
        )

    if server_mode == "development" or server_mode == "testing":
        asyncio.get_event_loop().set_debug(True)

    return app
