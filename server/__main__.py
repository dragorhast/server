"""
The primary entry point to the application.
"""
import asyncio

import aiomonitor
from aiohttp import web

from server import logger
from server.app import build_app
from server.monitor import Tap2GoMonitor
from server.version import __version__, name

if __name__ == '__main__':
    logger.info(f'Starting {name} %s!', __version__)
    app = build_app("spatialite://db.sqlite3")

    loop = asyncio.get_event_loop()
    aiomonitor.start_monitor(loop=loop, locals={"app": app}, monitor=Tap2GoMonitor)
    web.run_app(app)
