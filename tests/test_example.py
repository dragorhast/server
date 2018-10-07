from datetime import datetime, timedelta

from server.pricing import get_price


def test_pricing():
    assert get_price("", datetime.now() - timedelta(hours=6), "", datetime.now()) == 0.6
