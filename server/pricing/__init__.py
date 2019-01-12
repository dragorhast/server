"""
The pricing module determines the price for a bike in a given area, rented for a certain time,
when taking various sources on information into account such as time taken, location rented from,
location dropped of at, crime, economic data, etc.
"""

from datetime import datetime

HOURLY_PRICE = 0.1
DAILY_PRICE = 2
WEEKLY_PRICE = 10
MONTHLY_PRICE = 30


async def get_price(start_date: datetime, end_date: datetime, extra_cost=0.0) -> float:
    """
    Given a start location and end location, returns the price for a given ride.

    :return: The final price.
    """

    price = 0.0
    delta = end_date - start_date
    days = delta.days
    hours = delta.seconds // 60 // 60

    while days > 30:
        days -= 30
        price += 30

    while days > 7:
        days -= 7
        price += 10

    price += 2 * days
    price += 0.1 * hours

    price += extra_cost

    return round(price, 2)
