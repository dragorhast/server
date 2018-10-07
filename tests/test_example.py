from datetime import datetime, timedelta

from server.pricing import get_price


async def test_pricing():
    assert await get_price("eh47bl", datetime.now() - timedelta(hours=6), "le33aw", datetime.now()) == 0.6
