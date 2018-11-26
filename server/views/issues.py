"""
Handles all the issue CRUD
"""

from server.views.base import BaseView


class IssuesView(BaseView):
    """
    Gets the list of issues or adds a new issue.
    """
    url = "/issues"

    async def get(self):
        pass

    async def post(self):
        pass
