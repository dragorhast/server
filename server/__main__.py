"""
The primary entry point to the application.
"""

import weakref

from aiohttp import web

from server import api_root
from server.signals import register_signals
from server.views import register_views

app = web.Application()

# keep a track of all open bike connections
# and close them all when the server closes
app['bike_connections'] = weakref.WeakSet()


async def send_to_developer_portal(request):
    """Sends lost non-api requests to the developer portal."""
    raise web.HTTPFound(f' http://127.0.0.1:8000/lost.html?referrer={request.host}&next={api_root}/bikes')


app.router.add_get("/", send_to_developer_portal)
register_signals(app)
register_views(app.router, api_root)

if __name__ == '__main__':
    web.run_app(app)
