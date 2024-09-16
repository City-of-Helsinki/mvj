from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Iterable, Set, Union
from zoneinfo import ZoneInfo

from dateutil import tz as dateutil_tz

from ._times import AwareDateTime, TZAwareDateTime, check_is_aware
from .intset import IntegerSetSpecifier


@dataclass
class RecurrenceRule:
    timezone: ZoneInfo
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
            timezone=ZoneInfo(timezone),
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

    def get_next_events(
        self, start_time: datetime
    ) -> Iterable[Union[AwareDateTime, TZAwareDateTime]]:
        return get_next_events(self, start_time)


def get_next_events(
    rule: RecurrenceRule, start_time: datetime
) -> Iterable[Union[AwareDateTime, TZAwareDateTime]]:
    check_is_aware(start_time)

    tz = rule.timezone
    last_timestamps: Set[Union[AwareDateTime, TZAwareDateTime]] = set()

    for d in _iter_dates_from(rule, start_time.astimezone(tz).date()):
        timestamps: Set[Union[AwareDateTime, TZAwareDateTime]] = set()
        for t in _iter_times(rule):
            dt = datetime.combine(d, t)
            for timestamp in _get_possible_times(rule, dt, tz):
                if timestamp >= start_time:
                    timestamps.add(
                        # Subclass of datetime that has eq for offset-aware comparison.
                        # Used so that the same timestamp with different offset values
                        # are interpret as unique.
                        TZAwareDateTime.fromtimestamp(
                            timestamp.timestamp(), tz=timestamp.tzinfo
                        )
                    )

        # There might be entries in the timestamps set which were
        # already in the previous day's set, if DST change happens on
        # midnight, so remove those.
        timestamps -= last_timestamps
        # Sort the timestamps in UTC in order to preserve the correct time order.
        yield from sorted(timestamps, key=lambda dt: dt.astimezone(ZoneInfo("UTC")))

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
    rule: RecurrenceRule, naive_datetime: datetime, zoneinfo: ZoneInfo
) -> Iterable[Union[AwareDateTime, TZAwareDateTime]]:
    aware_datetime = AwareDateTime(naive_datetime.replace(tzinfo=zoneinfo))

    if not dateutil_tz.datetime_exists(aware_datetime):
        # If the datetime does not exist (due to DST transition), adjust it
        return [aware_datetime + timedelta(hours=1)]
    elif dateutil_tz.datetime_ambiguous(aware_datetime) and len(rule.hours) > 1:
        # If the datetime is ambiguous (due to DST transition), return both possibilities
        standard_time = aware_datetime.replace(fold=0)
        daylight_time = aware_datetime.replace(fold=1)
        daylight_and_standard_datetimes = [daylight_time, standard_time]
        return filter(
            lambda x: rule.matches_datetime(x), daylight_and_standard_datetimes
        )

    return [aware_datetime]
