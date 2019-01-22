"""
Issue Related Views
--------------------------

Handles all the issue CRUD
"""
from server.serializer import JSendSchema, JSendStatus
from server.serializer.decorators import returns
from server.serializer.models import IssueSchema
from server.service.issues import get_issues
from server.views.base import BaseView
from server.views.utils import match_getter


class IssuesView(BaseView):
    """
    Gets the list of issues or adds a new issue.
    """
    url = "/issues"
    issues_getter = match_getter(get_issues, "issues")

    @issues_getter
    @returns(JSendSchema.of(IssueSchema(only=(
        'id', 'user_id', 'user_url', 'bike_id', 'bike_url', 'time', 'description'
    ))))
    async def get(self, issues):
        return {
            "status": JSendStatus.SUCCESS,
            "data": [issue.serialize() for issue in issues]
        }
