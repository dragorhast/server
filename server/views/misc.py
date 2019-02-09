from aiohttp import web


async def redoc(request):
    """Sends lost non-api requests to the developer portal."""
    return web.FileResponse("server/static/redoc.html")


async def logo(request):
    return web.FileResponse("server/static/logo.svg")
