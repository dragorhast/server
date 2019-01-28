"""
Verify Token
------------

A number of API token verification strategies.
"""
import asyncio
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Dict

from aiohttp import ClientSession
from aiohttp.web_request import Request
from jose import jwt, ExpiredSignatureError, JWTError


class TokenVerificationError(Exception):
    pass


class TokenVerifier(ABC):

    @abstractmethod
    def verify_token(self, token):
        """
        Given a token, verifies it, returning the valid token or a token verification error.

        :raises TokenVerificationError: When the provided token is invalid.
        """


class FirebaseVerifier(TokenVerifier):
    """
    Verifies a firebase token.
    """

    _public_key_url = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
    _certificates: Dict[str, str]

    def __init__(self, audience):
        self._certificates = {}
        self.audience = audience

    async def _get_keys(self):
        async with ClientSession() as session:
            request = await session.get(self._public_key_url)
            self._certificates = await request.json()

    async def get_keys(self, update_period: timedelta = None):
        if update_period is None:
            await self._get_keys()
            return
        while True:
            await self._get_keys()
            await asyncio.sleep(update_period.total_seconds())

    def verify_token(self, token, verify_exp=True):
        if not self._certificates:
            raise TokenVerificationError("Server does not possess the verification certificates.")

        if not isinstance(token, str):
            raise TypeError(f"Token must be of type string, not {type(token)}")

        try:
            claims = jwt.decode(
                token,
                self._certificates,
                algorithms='RS256',
                audience=self.audience,
                options={'verify_exp': verify_exp}
            )
        except ExpiredSignatureError as e:
            raise TokenVerificationError("Token is expired.") from e
        except JWTError as e:
            raise TokenVerificationError("Token is invalid.") from e

        return claims.get("user_id")


class DummyVerifier(TokenVerifier):
    """
    Verifies a dummy token.
    """

    def verify_token(self, token: str) -> str:
        try:
            bytes.fromhex(token)
        except (ValueError, TypeError):
            raise TokenVerificationError("Not a valid hex string.")

        return token


def verify_token(request: Request):
    """
    Checks a view for the existence of a valid Authorization header.

    :param request: The view to check.
    :return: The valid token.
    :raises TokenVerificationError: When the Authorize header is invalid.
    """
    if "Authorization" not in request.headers:
        raise TokenVerificationError("You must supply your firebase token.")

    if not request.headers["Authorization"].startswith("Bearer "):
        raise TokenVerificationError("The Authorization header must be of the format \"Bearer $TOKEN\".")

    try:
        return request.app["token_verifier"].verify_token(request.headers["Authorization"][7:])
    except TokenVerificationError as error:
        raise error
