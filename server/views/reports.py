from collections import Counter
from datetime import timedelta
from re import fullmatch

from aiohttp_apispec import docs
from marshmallow import fields

from server.models import Issue
from server.models.issue import IssueStatus
from server.serializer import JSendStatus, returns, JSendSchema
from server.views.base import BaseView

ANNUAL_REGEX = "\/(?P<year>[0-9]{4})"
MONTHLY_REGEX = ANNUAL_REGEX + "(?:\-(?P<month>[0-9]{2}))?"
DAILY_REGEX = MONTHLY_REGEX + "(?:\-(?P<day>[0-9]{2}))?"


class AnnualReportView(BaseView):
    url = f"/report/annual{{filter:({ANNUAL_REGEX})?}}"

    @docs(summary="Get Annual Report")
    @returns(JSendSchema())
    async def get(self):
        """
        Gets annual reports for the given year. Accepts filters from ISO8601 dates.

        Example: ``/reports/2019``
        """

        filters = fullmatch(ANNUAL_REGEX, self.request.match_info["filter"])

        if filters:
            data = self.statistics_reporter.annual_report(**filters.groupdict())
        else:
            data = self.statistics_reporter.annual_report()

        return {
            "status": JSendStatus.SUCCESS,
            "data": data
        }


class MonthlyReportView(BaseView):
    url = f"/report/monthly{{filter:({MONTHLY_REGEX})?}}"

    @docs(summary="Get Monthly Report")
    @returns(JSendSchema())
    async def get(self):
        """
        Gets monthly reports for the given year or month. Accepts filters from ISO8601 dates.

        Example: ``/reports/2019`` or ``/reports/2012/06``
        """

        filters = fullmatch(MONTHLY_REGEX, self.request.match_info["filter"])

        if filters:
            data = self.statistics_reporter.monthly_report(**filters.groupdict())
        else:
            data = self.statistics_reporter.monthly_report()

        return {
            "status": JSendStatus.SUCCESS,
            "data": data
        }


class DailyReportView(BaseView):
    url = f"/report/daily{{filter:({DAILY_REGEX})?}}"

    @docs(summary="Get Daily Report")
    @returns(JSendSchema())
    async def get(self):
        """
        Gets daily reports for the given year, month, or day. Accepts filters from ISO8601 dates.

        Example: ``/reports/2019`` or ``/reports/2018/02/13``
        """

        filters = fullmatch(DAILY_REGEX, self.request.match_info["filter"])

        if filters:
            data = self.statistics_reporter.daily_report(**filters.groupdict())
        else:
            data = self.statistics_reporter.daily_report()

        return {
            "status": JSendStatus.SUCCESS,
            "data": data
        }


class CurrentReportView(BaseView):
    url = f"/report/current"

    @docs(summary="Get Current Report")
    @returns(JSendSchema.of(
        current_rentals=fields.Integer(),
        current_reservations=fields.Integer(),
        current_shortages=fields.Integer(),
        connected_bikes=fields.Integer(),
        active_bikes=fields.Integer(),
        active_issues=fields.Integer(),
        average_issue_resolution_time=fields.TimeDelta()
    ))
    async def get(self):
        """
        Retrieves some statistics about the system as it is now.
        """

        current_rentals = len(self.rental_manager._active_rentals)
        current_reservations = len(self.reservation_manager.reservations)
        connected_bikes = len(self.bike_connection_manager._bike_connections)
        active_bikes = Counter(self.bike_connection_manager._bike_locked.values())[False]
        current_shortages = 0
        for count, date in self.reservation_sourcer.shortages().values():
            current_shortages += count

        active_issues = 0
        closed_issues = 0
        issue_time = timedelta()
        async for issue in Issue.all():
            if issue.status != IssueStatus.CLOSED:
                active_issues += 1
            else:
                closed_issues += 1
                issue_time += issue.closed_at - issue.opened_at

        return {
            "status": JSendStatus.SUCCESS,
            "data": {
                "current_rentals": current_rentals,
                "current_reservations": current_reservations,
                "current_shortages": current_shortages,
                "connected_bikes": connected_bikes,
                "active_bikes": active_bikes,
                "active_issues": active_issues,
                "average_issue_resolution_time": issue_time / closed_issues if closed_issues > 0 else None,
            }
        }
