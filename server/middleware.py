"""
Middleware
----------
"""

from aiohttp import web
from aiohttp.abc import Request
from aiohttp.web_middlewares import middleware

from server.service.verify_token import verify_token, TokenVerificationError


@middleware
async def validate_token_middleware(request: Request, handler):
    """
    Ensures that any Authorization header given to the application is valid,
    and stores it on the request as the "token".
    """

    if "Authorization" in request.headers:
        try:
            request["token"] = verify_token(request)
        except TokenVerificationError as error:
            return web.json_response({
                "status": "fail",
                "data": {"authorization": error.args}
            })

    return await handler(request)
