import asyncio

from aiomonitor import Monitor
from firebase_admin.auth import AuthError

from server.models.user import UserType
from server.service.access.bikes import get_bikes, get_bike, set_bike_in_circulation
from server.service.access.users import get_users, set_user_admin
from server.service.manager.bike_connection_manager import BikeConnectionManager


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

    def do_get_bikes(self):
        """Get all bikes."""
        fetch = asyncio.run_coroutine_threadsafe(get_bikes(), self._loop)
        bikes = fetch.result()

        manager: BikeConnectionManager = self._locals["app"]["bike_location_manager"]

        for bike in bikes:
            location = manager.most_recent_location(bike)
            if location is not None:
                location, _, _ = location
                location = f"({location.x}, {location.y})"
            else:
                location = ""

            self._sout.write(f"- {bike} {'not ' if not bike.in_circulation else ''}in circulation {location}\n")

    def do_take_out_of_circulation(self, bike: str):
        """Take a bike out of circulation."""
        fetch = asyncio.run_coroutine_threadsafe(get_bike(identifier=bike), self._loop)
        bike = fetch.result()

        fetch = asyncio.run_coroutine_threadsafe(set_bike_in_circulation(bike, False), self._loop)
        result = fetch.result()

    def do_put_bike_into_circulation(self, bike: str):
        """Put bike in circulation."""
        fetch = asyncio.run_coroutine_threadsafe(get_bike(identifier=bike), self._loop)
        bike = fetch.result()

        fetch = asyncio.run_coroutine_threadsafe(set_bike_in_circulation(bike, True), self._loop)
        result = fetch.result()
