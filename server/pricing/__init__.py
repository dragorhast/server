"""
The pricing module determines the price for a bike in a given area, rented for a certain time,
when taking various sources on information into account such as time taken, location rented from,
location dropped of at, crime, economic data, etc.
"""

from datetime import datetime

HOURLY_PRICE = 2
DAILY_PRICE = 5
WEEKLY_PRICE = 25
MONTHLY_PRICE = 50


async def get_price(start_date: datetime, end_date: datetime, extra_cost=0.0) -> float:
    """
    Given a start location and end location, returns the price for a given ride.

    :return: The final price.
    """

    price = 0.0
    delta = end_date - start_date

    days = delta.days
    hours = delta.seconds / 60 / 60

    while days > 30:
        days -= 30
        price += MONTHLY_PRICE

    while days > 7:
        days -= 7
        price += WEEKLY_PRICE

    price += DAILY_PRICE * days
    price += HOURLY_PRICE * hours
    price += extra_cost

    return round(price, 2)
