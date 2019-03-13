import asyncio
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, List

from server.models import StatisticsReport
from server.service.manager.rental_manager import RentalManager, RentalEvent
from server.service.manager.reservation_manager import ReservationManager, ReservationEvent


class StatisticsReporter:

    def __init__(self, rental_manager: RentalManager, reservation_manager: ReservationManager):
        self._rental_manager = rental_manager
        self._reservation_manager = reservation_manager

        self._rental_manager.hub.subscribe(RentalEvent.rental_started, self._rental_started)
        self._rental_manager.hub.subscribe(RentalEvent.rental_ended, self._rental_ended)
        self._reservation_manager.hub.subscribe(ReservationEvent.opened_reservation, self._opened_reservation)
        self._reservation_manager.hub.subscribe(ReservationEvent.cancelled_reservation, self._cancelled_reservation)

        self._rentals_started: Dict[date, int] = defaultdict(int)
        self._rentals_ended: Dict[date, int] = defaultdict(int)
        self._reservations_started: Dict[date, int] = defaultdict(int)
        self._reservations_cancelled: Dict[date, int] = defaultdict(int)
        self._distance_travelled: Dict[date, float] = defaultdict(float)
        self._revenue: Dict[date, float] = defaultdict(float)

    async def run(self):
        """Sleeps until midnight and then saves a statistics report for that day."""
        while True:
            today = date.today()
            tomorrow = today + timedelta(days=1)
            midnight = datetime(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day)
            await asyncio.sleep((midnight - datetime.now()).seconds)

            await StatisticsReport.create(
                date=today,
                rentals_started=self._rentals_started[today],
                rentals_ended=self._rentals_ended[today],
                reservations_started=self._reservations_started[today],
                reservations_cancelled=self._reservations_cancelled[today],
                distance_travelled=self._distance_travelled[today],
                revenue=self._revenue[today],
            )

    async def _rebuild(self):
        for report in await StatisticsReport.all():
            self._rentals_started[report.date] += report.rentals_started
            self._rentals_ended[report.date] += report.rentals_ended
            self._reservations_started[report.date] += report.reservations_started
            self._reservations_cancelled[report.date] += report.reservations_cancelled
            self._distance_travelled[report.date] += report.distance_travelled
            self._revenue[report.date] += report.revenue

    def _rental_started(self, user, bike, location):
        self._rentals_started[date.today()] += 1

    def _rental_ended(self, user, bike, location, price, distance):
        today = date.today()
        self._rentals_ended[today] += 1
        self._revenue[today] += price
        self._distance_travelled[today] += distance

    def _opened_reservation(self, pickup, user, time):
        self._reservations_started[date.today()] += 1

    def _cancelled_reservation(self, pickup, user, time):
        self._reservations_cancelled[date.today()] += 1

    def daily_report(self, year: int = None, month: int = None, day_nr: int = None) -> List[Dict]:

        dates = (x for x in self._rentals_started.keys())

        if year is not None:
            dates = (x for x in dates if x.year == int(year))

        if month is not None:
            dates = (x for x in dates if x.month == int(month))

        if day_nr is not None:
            dates = (x for x in dates if x.day == int(day_nr))

        data_days = []

        for day in dates:
            data_days.append({
                "date": day,
                "incomplete": day == day.today(),
                "rentals_started": self._rentals_started[day],
                "rentals_ended": self._rentals_ended[day],
                "reservations_started": self._reservations_started[day],
                "reservations_cancelled": self._reservations_cancelled[day],
                "distance_travelled": self._distance_travelled[day],
                "revenue": self._revenue[day]
            })

        return data_days

    def monthly_report(self, year=None, month=None):
        dates = (x for x in self._rentals_started.keys())

        if year is not None:
            dates = (x for x in dates if x.year == int(year))

        if month is not None:
            dates = (x for x in dates if x.month == int(month))

        data = {}

        for day in dates:
            month = day.replace(day=1)
            if month not in data:
                data[month] = {
                    "date": month, "rentals_started": 0, "rentals_ended": 0, "reservations_started": 0,
                    "reservations_cancelled": 0, "distance_travelled": 0, "revenue": 0
                }

            data[month]["rentals_started"] += self._rentals_started[day]
            data[month]["rentals_ended"] += self._rentals_ended[day]
            data[month]["reservations_started"] += self._reservations_started[day]
            data[month]["reservations_cancelled"] += self._reservations_cancelled[day]
            data[month]["distance_travelled"] += self._distance_travelled[day]
            data[month]["revenue"] += self._revenue[day]

        return list(data.values())

    def annual_report(self, year=None):
        dates = (x for x in self._rentals_started.keys())

        if year is not None:
            dates = (x for x in dates if x.year == int(year))

        data = {}

        for day in dates:
            year = day.replace(month=1, day=1)
            if year not in data:
                data[year] = {
                    "date": year, "rentals_started": 0, "rentals_ended": 0, "reservations_started": 0,
                    "reservations_cancelled": 0, "distance_travelled": 0, "revenue": 0
                }

            data[year]["rentals_started"] += self._rentals_started[day]
            data[year]["rentals_ended"] += self._rentals_ended[day]
            data[year]["reservations_started"] += self._reservations_started[day]
            data[year]["reservations_cancelled"] += self._reservations_cancelled[day]
            data[year]["distance_travelled"] += self._distance_travelled[day]
            data[year]["revenue"] += self._revenue[day]

        return list(data.values())
