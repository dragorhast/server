"""
The primary entry point to the application.
"""
import weakref

from aiohttp import web

from server.signals import close_bike_connections
from server.views import register_all

app = web.Application()

# keep a track of all open bike connections
# and close them all when the server closes
app['bike_connections'] = weakref.WeakSet()
app.on_shutdown.append(close_bike_connections)

register_all(app.router, "/api/v1")

if __name__ == '__main__':
    web.run_app(app)
