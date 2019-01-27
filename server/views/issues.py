"""
Issue Related Views
--------------------------

Handles all the issue CRUD
"""
from typing import List

from server.models import Issue
from server.permissions.decorators import requires
from server.permissions.permissions import UserIsAdmin
from server.serializer import JSendSchema, JSendStatus
from server.serializer.decorators import returns
from server.serializer.models import IssueSchema
from server.service.issues import get_issues
from server.service.users import get_user
from server.views.base import BaseView
from server.views.utils import match_getter, GetFrom


class IssuesView(BaseView):
    """
    Gets the list of issues or adds a new issue.
    """
    url = "/issues"
    with_issues = match_getter(get_issues, "issues")
    with_admin = match_getter(get_user, "user", firebase_id=GetFrom.AUTH_HEADER)

    @with_admin
    @with_issues
    @requires(UserIsAdmin())
    @returns(JSendSchema.of(IssueSchema(only=(
        'id', 'user_id', 'user_url', 'bike_id', 'bike_url', 'time', 'description'
    )), many=True))
    async def get(self, user, issues: List[Issue]):
        return {
            "status": JSendStatus.SUCCESS,
            "data": [issue.serialize(self.request.app.router) for issue in issues]
        }
