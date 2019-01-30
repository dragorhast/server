"""
This module contains the various permission types. A permission is essentially
just an object (either function or class) that can be called asynchronously
and raises a RoutePermissionError in the case of a failed permission.
"""

from server.permissions.bikes import BikeIsConnected, BikeNotBroken, BikeNotInUse
from server.permissions.users import UserMatchesFirebase, UserIsRentingBike, UserIsAdmin
from server.permissions.util import ValidToken
from server.permissions.decorators import requires
