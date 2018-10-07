"""
The pricing module determines the price for a bike in a given area, rented for a certain time,
when taking various sources on information into account such as time taken, location rented from,
location dropped of at, crime, economic data, etc.
"""
from math import floor

from typing import Optional
from datetime import datetime

HOURLY_PRICE = 0.1
DAILY_PRICE = 2
WEEKLY_PRICE = 10
MONTHLY_PRICE = 30


def get_price(start_postcode, start: datetime, end_postcode, end: datetime) -> float:
    price = 0
    delta = end - start

    while delta.days > 30:
        delta.days -= 30
        price += 30

    while delta.days > 7:
        delta.days -= 7
        price += 10

    price += 2 * delta.days
    price += 0.1 * (delta.seconds // 60 // 60)

    return round(price, 2)
