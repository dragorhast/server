import asyncio

from aiomonitor import Monitor
from firebase_admin.auth import AuthError

from server.models.user import UserType
from server.service.access.users import get_users, set_user_admin


class Tap2GoMonitor(Monitor):

    def do_set_user_level(self, user_id: str, user_type: str):
        """Set's a user's admin level to the provided value."""
        user_id = int(user_id)

        try:
            user_type = UserType(user_type)
        except ValueError as e:
            self._sout.write(f"{e}: valid values are {', '.join(x.value for x in UserType)}\n")
            return

        try:
            fetch = asyncio.run_coroutine_threadsafe(set_user_admin(user_id, user_type), self._loop)
            user = fetch.result()
        except AuthError as e:
            self._sout.write(f"{e}\n")
        else:
            self._sout.write(f"User {user} set to level {user_type.value}.\n")

    def do_search_user(self, name: str):
        """Search a user by name."""
        fetch = asyncio.run_coroutine_threadsafe(get_users(name=name), self._loop)
        users = fetch.result()

        for user in users:
            self._sout.write(f"- {user}\n")
