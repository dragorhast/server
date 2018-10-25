from datetime import datetime, timedelta

import pytest

from server.pricing import get_price


@pytest.mark.asyncio
async def test_pricing():
    assert await get_price("eh47bl", datetime.now() - timedelta(hours=6), "le33aw", datetime.now()) == 4.55
