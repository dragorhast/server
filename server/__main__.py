"""
The primary entry point to the application.
"""
import weakref

import sentry_sdk
import uvloop
from aiohttp import web
from aiohttp_sentry import SentryMiddleware

from server import api_root, server_mode, logger
from server.signals import register_signals
from server.version import __version__
from server.views import register_views, send_to_developer_portal

logger.info(f'Starting tap2go-server {__version__}!')

# set up app and install uvloop
app = web.Application(middlewares=[SentryMiddleware()])
uvloop.install()

# keep a track of all open bike connections
app['bike_connections'] = weakref.WeakSet()

# set database stuff
app['database_uri'] = 'sqlite://db.sqlite3'

# set up the background tasks
register_signals(app)

# register views
register_views(app.router, api_root)
app.router.add_get("/", send_to_developer_portal)

# set up sentry exception tracking
if server_mode != "development":
    sentry_sdk.init(
        dsn="https://ac31a26ce42c434e9ce1bde34768631d@sentry.io/1296249",
        environment=server_mode,
        release=f"server@{__version__}"
    )

if __name__ == '__main__':
    web.run_app(app)
