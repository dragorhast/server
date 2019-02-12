"""
Some tests for the expects and returns decorators.

..todo:: create a separate app to test them on,
         instead of relying on the routes
"""

from aiohttp.test_utils import TestClient

from server.serializer import JSendSchema, JSendStatus


class TestExpectDecorator:

    async def test_expects_no_data(self, client: TestClient):
        """Assert that trying to register a bike with no data fails."""
        resp = await client.post('/api/v1/bikes')
        data = JSendSchema().load(await resp.json())
        assert "only accepts JSON" in data["data"]["message"]
        assert data["status"] == JSendStatus.FAIL
        assert "schema" in data["data"]

    async def test_expects_malformed_json(self, client: TestClient):
        """Assert that trying to register a bike with no data fails."""
        resp = await client.post('/api/v1/bikes', data="[", headers={"Content-Type": "application/json"})
        data = JSendSchema().load(await resp.json())
        assert data["status"] == JSendStatus.FAIL
        assert "Could not parse" in data["data"]["message"]

    async def test_expects_invalid_data(self, client: TestClient):
        """Assert that trying to register a bike with invalid data fails."""
        resp = await client.post('/api/v1/bikes', json={"wrong": "data"}, headers={"Content-Type": "application/json"})
        data = JSendSchema().load(await resp.json())
        assert data["status"] == JSendStatus.FAIL
        assert "did not validate" in data["data"]["message"]
        assert "public_key" in data["data"]["errors"]


class TestReturnsDecorator:
    pass
