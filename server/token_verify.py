from abc import ABC, abstractmethod
from typing import Dict

from aiohttp import ClientSession
from jose.jwt import decode


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

    def verify_token(self, token):
        if not self._certificates:
            raise Exception

        claims = decode(
            token,
            next(self._certificates.keys()),
            algorithms=['RS256'],
            audience=self.audience,
            issuer=f"https://securetoken.google.com/{self.audience}"
        )

        return claims.get("sub")


class DummyVerifier(TokenVerifier):
    """
    Verifies a dummy token.
    """

    def verify_token(self, token) -> str:
        try:
            bytes.fromhex(token)
        except ValueError:
            raise TokenVerificationError("Not a valid hex string.")

        return token


def verify_token(request):
    """
    Checks a view for the existence of a valid Authorization header.

    :param request: The view to check.
    :return: The valid token.
    :raises TokenVerificationError: When the Authorize header is invalid.
    """
    if (
        "Authorization" not in request.headers or
        not request.headers["Authorization"].startswith("Bearer ")
    ):
        raise TokenVerificationError("You must supply your firebase token.")

    try:
        return verifier.verify_token(request.headers["Authorization"][7:])
    except TokenVerificationError as error:
        raise error


# verifier = FirebaseVerifier("dragorhast-420")
verifier = DummyVerifier()
