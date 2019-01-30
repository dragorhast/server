from typing import Union

from server.models import User, Bike
from server.models.issue import Issue


async def get_issues(*, user: Union[User, int] = None, bike: Union[Bike, int, str] = None, is_active: bool = None):
    options = {}

    if isinstance(user, User):
        options["user"] = user
    elif isinstance(user, int):
        options["user_id"] = user

    if isinstance(bike, Bike):
        options["bike"] = bike
    elif isinstance(bike, int):
        options["bike_id"] = bike
    elif isinstance(bike, str):
        options["bike__public_key_hex__startswith"] = bike

    if is_active is not None:
        options["is_active"] = is_active

    return await Issue.filter(**options).prefetch_related('bike')


async def get_issue(iid: int):
    return await Issue.filter(id=iid).prefetch_related('bike').first()


async def get_broken_bikes():
    """Gets the list of all broken bikes ie. those with active issues."""
    active_issues = await Issue.filter(is_active=True).prefetch_related('bike')
    bikes = {}

    for issue in active_issues:
        bikes[issue.bike.id] = issue.bike

    return bikes.values()


async def open_issue(user: Union[User, int], description: str, bike: Union[User, int] = None):
    options = {
        "description": description
    }

    if isinstance(user, User):
        options["user"] = user
    else:
        options["user_id"] = user

    if isinstance(bike, Bike):
        options["bike"] = bike
    elif isinstance(bike, int):
        options["bike_id"] = bike

    return await Issue.create(**options)


async def close_issue(issue: Union[Issue, int]):
    if isinstance(issue, int):
        issue = await Issue.filter(id=issue).first()

    issue.is_active = False
    await issue.save()
