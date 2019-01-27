from server.serializer import JSendSchema
from server.serializer.models import IssueSchema
from server.service.issues import open_issue


class TestIssuesView:

    async def test_get_issues(self, client, random_admin):
        schema = JSendSchema.of(IssueSchema(many=True))
        await open_issue(random_admin, "test issue!")
        resp = await client.get('/api/v1/issues', headers={"Authorization": f"Bearer {random_admin.firebase_id}"})

        data = schema.load(await resp.json())
        assert len(data["data"]) == 1
