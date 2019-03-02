from re import fullmatch

from aiohttp_apispec import docs

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
