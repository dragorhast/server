"""
The primary entry point to the application.
"""
from datetime import datetime, timedelta

from aiohttp import web

from server.pricing import get_price


async def handle(request):
    """
    An example request handler.
    """
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)


async def price(request):
    """
    An example handler.
    """
    postcode = request.match_info.get('postcode', "EH47BL")
    hours = int(request.match_info.get('hours', "1"))
    return web.Response(
        text=str(await get_price("eh47bl", datetime.now() - timedelta(hours=hours), postcode, datetime.now()))
    )


APP = web.Application()

APP.add_routes([
    web.get('/', handle),
    web.get('/{name}', handle),
    web.get('/{postcode}/{hours}', price)
])
