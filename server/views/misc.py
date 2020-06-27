import os
from pathlib import Path

from aiohttp import web

PACKAGE_FOLDER = Path(os.path.dirname(__file__)) / ".."


async def redoc(request):
    """Sends lost non-api requests to the developer portal."""
    return web.FileResponse(PACKAGE_FOLDER / "static" / "redoc.html")


async def logo(request):
    return web.FileResponse(PACKAGE_FOLDER / "static" / "logo.svg")
