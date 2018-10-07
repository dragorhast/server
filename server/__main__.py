"""
The primary entry point to the application.
"""

from aiohttp import web


async def handle(request):
    """
    An example request handler.
    """
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)


APP = web.Application()

APP.add_routes([
    web.get('/', handle),
    web.get('/{name}', handle)
])

web.run_app(APP)
