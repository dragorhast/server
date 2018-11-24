"""
The primary entry point to the application.
"""

from aiohttp import web

from server.views import register_all

app = web.Application()
register_all(app.router, "/api/v1")

if __name__ == '__main__':
    web.run_app(app)
