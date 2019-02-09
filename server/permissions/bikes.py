from aiohttp.web_urldispatcher import View

from server.models import Bike
from server.permissions.permission import RoutePermissionError, Permission
from server.service.access.issues import get_issues


class BikeNotInUse(Permission):
    """Asserts that the given bike is not being used."""

    async def __call__(self, view: View, bike: Bike, **kwargs):
        if view.rental_manager.is_in_use(bike):
            raise RoutePermissionError("The requested bike is in use.")


class BikeNotBroken(Permission):
    """Asserts that the given bike has no active issues."""

    def __init__(self, *, max_issues=0):
        """The maximum number of issues before denying access."""
        self.max_issues = max_issues

    async def __call__(self, view: View, bike: Bike, **kwargs):
        if len(await get_issues(bike=bike, is_active=True)) > self.max_issues:
            raise RoutePermissionError("The requested bike is broken.")


class BikeIsConnected(Permission):

    async def __call__(self, view: View, bike: Bike, **kwargs):
        if not view.bike_connection_manager.is_connected(bike):
            raise RoutePermissionError("The requested bike is not connected.")
