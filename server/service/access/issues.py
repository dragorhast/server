"""
Issues
======
"""
from collections import defaultdict
from typing import Union, Tuple, List, Dict, Set

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


async def get_broken_bikes() -> Tuple[Set[str], Dict[str, Bike], Dict[str, List[Issue]]]:
    """
    Gets the list of all broken bikes ie. those with active issues.

    :returns: A tuple of the list of identifiers,
     a dictionary mapping the identifier to its bike,
     and a dictionary mapping the identifier to its list of issues
    """
    active_issues = await Issue.filter(is_active=True, bike_id__not_isnull=True).prefetch_related('bike')

    identifiers = set()
    bikes = {}
    issues = defaultdict(list)

    for issue in active_issues:
        identifier = issue.bike.identifier
        identifiers.add(identifier)
        bikes[identifier] = issue.bike
        issues[identifier].append(issue)

    return identifiers, bikes, issues


async def open_issue(user: Union[User, int], description: str, bike: Bike = None):
    options = {
        "description": description
    }

    if isinstance(user, User):
        options["user"] = user
    else:
        options["user_id"] = user

    if bike is not None:
        options["bike"] = bike

    issue = await Issue.create(**options)
    issue.bike = bike
    return issue


async def close_issue(issue: Union[Issue, int]):
    if isinstance(issue, int):
        issue = await Issue.filter(id=issue).first()

    issue.is_active = False
    await issue.save()
