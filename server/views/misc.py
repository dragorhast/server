from aiohttp import web

from server import api_root


async def send_to_developer_portal(request):
    """Sends lost non-api requests to the developer portal."""
    raise web.HTTPFound(f' http://tap2go-server.netlify.com/lost.html?referrer={request.host}&next={api_root}/bikes')
