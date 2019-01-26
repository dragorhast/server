from typing import Union

from server.models import User, Bike
from server.models.issue import Issue


async def get_issues(*, user: Union[User, int] = None):
    options = {}
    if isinstance(user, User):
        options["user"] = user
    elif isinstance(user, int):
        options["user_id"] = user

    return await Issue.filter(**options)


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


