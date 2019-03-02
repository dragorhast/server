"""
Issue Related Views
--------------------------

Handles all the issue CRUD
"""
from typing import List

from aiohttp_apispec import docs

from server.models import Issue
from server.permissions.decorators import requires
from server.permissions.users import UserIsAdmin
from server.serializer import JSendSchema, JSendStatus
from server.serializer.decorators import returns
from server.serializer.fields import Many
from server.serializer.models import IssueSchema
from server.service.access.issues import get_issues, get_issue
from server.service.access.users import get_user
from server.views.base import BaseView
from server.views.decorators import match_getter, GetFrom


class IssuesView(BaseView):
    """
    Gets the list of issues or adds a new issue.
    """
    url = "/issues"
    with_issues = match_getter(get_issues, "issues")
    with_admin = match_getter(get_user, "user", firebase_id=GetFrom.AUTH_HEADER)

    @with_admin
    @with_issues
    @docs(summary="Get All Open Issues")
    @requires(UserIsAdmin())
    @returns(JSendSchema.of(issues=Many(IssueSchema(exclude=('user', 'bike')))))
    async def get(self, user, issues: List[Issue]):
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"issues": [issue.serialize(self.request.app.router) for issue in issues]}
        }


class IssueView(BaseView):
    """
    Gets an issue by its id
    """

    url = "/issues/{id}"
    with_issue = match_getter(get_issue, "issue", iid="id")

    @with_issue
    @docs(summary="Get An Open Issue")
    @returns(JSendSchema.of(issue=IssueSchema()))
    async def get(self, issue):
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"issue": issue.serialize(self.request.app.router)}
        }
