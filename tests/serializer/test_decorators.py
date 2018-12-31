from aiohttp.test_utils import TestClient


class TestExpectDecorator:

    async def test_expects_no_data(self, client: TestClient):
        """Assert that trying to register a bike with no data fails."""
        resp = await client.post('/api/v1/bikes')
        text = await resp.text()
        pass

    async def test_expects_malformed_json(self, client: TestClient):
        """Assert that trying to register a bike with no data fails."""
        resp = await client.post('/api/v1/bikes', data="[", headers={"Content-Type": "application/json"})
        text = await resp.text()
        pass


class TestReturnsDecorator:
    pass
