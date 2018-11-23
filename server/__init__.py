"""
The primary entry point to the application.
"""

from aiohttp import web

from server.pricing import get_price
from server.views import register_all

app = web.Application()
register_all(app.router, "/api/v1")
