import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from firebase_admin import initialize_app
from firebase_admin.auth import set_custom_user_claims
from firebase_admin.credentials import Certificate

from server.models import User
from server.models.user import UserType

FIREBASE_EXECUTOR = ThreadPoolExecutor(max_workers=4)


class FirebaseClaimManager:
    """Updates custom claims in firebase by wrapping the firebase admin SDK with asyncio."""

    def __init__(self, credentials):
        self._credentials = Certificate(credentials)
        self._init = False
        self._loop = None
        self._app = None

    async def initialize(self):
        if self._init:
            return
        else:
            self._loop = asyncio.get_event_loop()
            self._app = await self._loop.run_in_executor(FIREBASE_EXECUTOR, partial(initialize_app, self._credentials))
            self._init = True

    async def set_user_type(self, user: User, user_type: UserType):
        await self.initialize()
        await self._loop.run_in_executor(FIREBASE_EXECUTOR, partial(set_custom_user_claims, user.firebase_id, {
            "user_type": user_type.value
        }))
