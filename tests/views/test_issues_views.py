from server.serializer import JSendSchema, JSendStatus
from server.serializer.fields import Many
from server.serializer.models import IssueSchema
from server.service.access.issues import open_issue


class TestIssuesView:

    async def test_get_issues(self, client, random_admin):
        schema = JSendSchema.of(issues=Many(IssueSchema()))
        await open_issue(random_admin, "test issue!")
        resp = await client.get('/api/v1/issues', headers={"Authorization": f"Bearer {random_admin.firebase_id}"})

        data = schema.load(await resp.json())
        assert len(data["data"]["issues"]) == 1


class TestIssueView:

    async def test_get_issue(self, client, random_admin):
        issue = await open_issue(random_admin, "An issue!")
        response = await client.get(f"/api/v1/issues/{issue.id}", headers={"Authorization": f"Bearer {random_admin.firebase_id}"})
        response_data = JSendSchema.of(issue=IssueSchema()).load(await response.json())
        assert response_data["status"] == JSendStatus.SUCCESS
        assert response_data["data"]["issue"]["id"] == issue.id
