from server.models.issue import Issue, IssueStatus
from server.service.access.issues import get_issues, open_issue, update_issue, get_broken_bikes


class TestIssues:

    async def test_get_issues(self, random_user):
        issue = await Issue.create(user=random_user, description="I don't like it!")
        assert issue in await get_issues()

    async def test_get_issues_for_user(self, random_user, random_admin):
        issue = await Issue.create(user=random_user, description="I'm a big fan!")
        issue2 = await Issue.create(user=random_admin, description="I'm a boss!")

        user_issues = await get_issues(user=random_user)
        assert issue in user_issues
        assert issue2 not in user_issues

    async def test_open_issue(self, random_user):
        issue = await open_issue(random_user, "Hello!")
        assert issue == await Issue.first()

    async def test_open_issue_with_bike(self, random_user, random_bike):
        issue = await open_issue(random_user, "Bad bike!", random_bike)
        added_issue = await Issue.first().prefetch_related('bike')
        assert issue == added_issue
        assert random_bike == added_issue.bike

    async def test_close_issue(self, random_user):
        issue = await Issue.create(user=random_user, description="Uh oh!")
        await update_issue(issue, IssueStatus.CLOSED, resolution="Fixed!")
        assert await Issue.filter(status=IssueStatus.CLOSED).count() == 1

    async def test_close_issue_by_id(self, random_user):
        issue = await Issue.create(user=random_user, description="Uh oh!")
        await update_issue(issue.id, IssueStatus.CLOSED, resolution="Fixed!")
        assert await Issue.filter(status=IssueStatus.CLOSED).count() == 1

    async def test_get_broken_bikes(self, random_bike_factory, random_user, bike_connection_manager):
        bike1 = await random_bike_factory(bike_connection_manager)
        bike2 = await random_bike_factory(bike_connection_manager)
        bike3 = await random_bike_factory(bike_connection_manager)

        issue = await open_issue(random_user, "My bike sucks!", bike1)
        broken_bikes = await get_broken_bikes()

        bikes, issues = zip(*broken_bikes)
        assert bike1 in bikes
