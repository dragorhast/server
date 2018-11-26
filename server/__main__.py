"""
The primary entry point to the application.
"""

import weakref

from aiohttp import web

from server.signals import register_signals
from server.views import register_views

app = web.Application()

# keep a track of all open bike connections
# and close them all when the server closes
app['bike_connections'] = weakref.WeakSet()

register_signals(app)
register_views(app.router, "/api/v1")

if __name__ == '__main__':
    web.run_app(app)
