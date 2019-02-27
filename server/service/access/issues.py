"""
Issues
======
"""
from collections import defaultdict
from typing import Union, Tuple, List, Dict, Set

from server.models import User, Bike
from server.models.issue import Issue, IssueStatus


async def get_issues(*, user: Union[User, int] = None, bike: Union[Bike, int, str] = None, is_active: bool = None):
    """
    Gets all the issues for either the given user, the given bike, or both.

    :param user: The user.
    :param bike: The bike.
    :param is_active: If true, only return issues that are open or in review. False means only closed issues.
    :return:
    """
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
        options["status__not" if is_active else "status"] = IssueStatus.CLOSED

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
    active_issues = await Issue.filter(status__not=IssueStatus.CLOSED, bike_id__not_isnull=True).prefetch_related(
        'bike', 'bike__state_updates'
    )

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


async def review_issue(issue: Union[Issue, int]):
    if isinstance(issue, int):
        issue = await Issue.filter(id=issue).first()

    issue.status = IssueStatus.CLOSED
    await issue.save()


async def close_issue(issue: Union[Issue, int]):
    if isinstance(issue, int):
        issue = await Issue.filter(id=issue).first()

    issue.status = IssueStatus.CLOSED
    await issue.save()
