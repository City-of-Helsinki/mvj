from dataclasses import dataclass
from datetime import date, datetime, time, tzinfo
from typing import Iterable, Set, Union

import pytz

from ._times import AwareDateTime, check_is_aware, make_aware
from .intset import IntegerSetSpecifier


@dataclass
class RecurrenceRule:
    timezone: tzinfo
    years: IntegerSetSpecifier
    months: IntegerSetSpecifier
    days_of_month: IntegerSetSpecifier
    weekdays: IntegerSetSpecifier
    hours: IntegerSetSpecifier
    minutes: IntegerSetSpecifier

    @classmethod
    def create(
        cls,
        timezone: str,
        years: str = "*",
        months: str = "*",
        days_of_month: str = "*",
        *,
        weekdays: str = "*",
        hours: str = "*",
        minutes: str = "*",
    ) -> "RecurrenceRule":
        return cls(
            timezone=pytz.timezone(timezone),
            years=IntegerSetSpecifier(years, 1970, 2200),
            months=IntegerSetSpecifier(months, 1, 12),
            days_of_month=IntegerSetSpecifier(days_of_month, 1, 31),
            weekdays=IntegerSetSpecifier(weekdays, 0, 6),
            hours=IntegerSetSpecifier(hours, 0, 23),
            minutes=IntegerSetSpecifier(minutes, 0, 59),
        )

    def matches_datetime(self, dt: datetime) -> bool:
        return self.matches_date(dt) and self.matches_time(dt.time())

    def matches_date(self, d: date) -> bool:
        return (
            d.year in self.years
            and d.month in self.months
            and d.day in self.days_of_month
            and self.matches_weekday(d)
        )

    def matches_weekday(self, dt: Union[date, datetime]) -> bool:
        if self.weekdays.is_total():
            return True
        python_weekday = dt.weekday()  # Monday = 0, Sunday = 6
        weekday = (python_weekday + 1) % 7  # Monday = 1, Sunday = 0
        return weekday in self.weekdays

    def matches_time(self, t: time) -> bool:
        return t.hour in self.hours and t.minute in self.minutes

    def get_next_events(self, start_time: datetime) -> Iterable[AwareDateTime]:
        return get_next_events(self, start_time)


def get_next_events(
    rule: RecurrenceRule, start_time: datetime
) -> Iterable[AwareDateTime]:
    check_is_aware(start_time)

    tz = rule.timezone
    last_timestamps: Set[AwareDateTime] = set()

    for d in _iter_dates_from(rule, start_time.astimezone(tz).date()):
        timestamps: Set[AwareDateTime] = set()
        for t in _iter_times(rule):
            dt = datetime.combine(d, t)
            for timestamp in _get_possible_times(rule, dt, tz):
                if timestamp >= start_time:
                    timestamps.add(timestamp)

        # There might be entries in the timestamps set which were
        # already in the previous day's set, if DST change happens on
        # midnight, so remove those.
        timestamps -= last_timestamps

        yield from sorted(timestamps)

        last_timestamps = timestamps


def _iter_dates_from(rule: RecurrenceRule, start_date: date) -> Iterable[date]:
    for year in rule.years:
        if year < start_date.year:
            continue

        for month in rule.months:
            if (year, month) < (start_date.year, start_date.month):
                continue

            for day in rule.days_of_month:
                try:
                    d = date(year, month, day)
                except ValueError:  # day out of range for month
                    continue  # Skip non-existing dates

                if d >= start_date and rule.matches_weekday(d):
                    yield d


def _iter_times(rule: RecurrenceRule) -> Iterable[time]:
    for hour in rule.hours:
        for minute in rule.minutes:
            yield time(hour, minute)


def _get_possible_times(
    rule: RecurrenceRule, naive_datetime: datetime, tz: tzinfo
) -> Iterable[AwareDateTime]:
    try:
        return [make_aware(naive_datetime, tz)]
    except pytz.AmbiguousTimeError:
        dsts = [True, False] if len(rule.hours) > 1 else [True]
        timestamps = (make_aware(naive_datetime, tz, is_dst=dst) for dst in dsts)
        return [x for x in timestamps if rule.matches_datetime(x)]
    except pytz.NonExistentTimeError:
        return [make_aware(naive_datetime, tz, is_dst=True)]
