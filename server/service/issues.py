from typing import Union

from server.models import User, Bike
from server.models.issue import Issue


async def get_issues():
    return await Issue.all()


async def create_issue(user: Union[User, int], description: str, bike: Union[User, int] = None):
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
