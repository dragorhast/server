"""
The primary entry point to the application.
"""

from aiohttp import web

from server import logger
from server.app import build_app
from server.version import __version__

if __name__ == '__main__':
    logger.info('Starting tap2go-server %s!', __version__)
    app = build_app("sqlite://db.sqlite3")
    web.run_app(app)
