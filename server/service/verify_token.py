"""
Verify Token
------------
"""

from abc import ABC, abstractmethod
from typing import Dict

from aiohttp import ClientSession
from jose import jwt, ExpiredSignatureError, JWTError


class TokenVerificationError(Exception):
    pass


class TokenVerifier(ABC):

    @abstractmethod
    def verify_token(self, token):
        pass


class FirebaseVerifier(TokenVerifier):
    """
    Verifies a firebase token.

    .. todo:: implement
    """

    _public_key_url = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
    _certificates: Dict[str, str]

    def __init__(self, audience):
        self._certificates = {}
        self.audience = audience

    async def get_key(self):
        async with ClientSession() as session:
            request = await session.get(self._public_key_url)
            self._certificates = await request.json()

    def verify_token(self, token, verify_exp=True):
        if not self._certificates:
            raise TokenVerificationError("You must fetch the certs.")

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
            raise TokenVerificationError("Token could not be parsed.") from e

        return claims.get("sub")


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


def verify_token(request):
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
        return verifier.verify_token(request.headers["Authorization"][7:])
    except TokenVerificationError as error:
        raise error


# verifier = FirebaseVerifier("dragorhast-420")
verifier = DummyVerifier()
