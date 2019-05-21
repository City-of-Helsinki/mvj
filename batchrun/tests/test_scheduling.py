from datetime import timedelta

import pytest
from dateutil.parser import parse as parse_datetime

from ..scheduling import RecurrenceRule, get_next_events


def rr(
        time_spec: str,
        weekdays: str = '*',
        tz: str = 'Europe/Helsinki',
) -> RecurrenceRule:
    """
    Create recurrence rule with a short formula.

    The time_spec should be either in "Y M D h m" or "M D h m" format,
    where Y is spec for years, M for months, D for days of month, h for
    hours and m for minutes.
    """
    spec_parts = time_spec.split()
    if len(spec_parts) == 5:
        years = spec_parts[0]
        spec_parts = spec_parts[1:]
    else:
        years = '*'
    (months, days_of_month, hours, minutes) = spec_parts

    return RecurrenceRule.create(
        tz, years, months, days_of_month,
        weekdays=weekdays, hours=hours, minutes=minutes)


GET_NEXT_EVENTS_CASES = {
    '3 months': {
        'rule': rr('2019 03-05 1 1 23'),
        'start': parse_datetime('2019-01-01 00:00 EET'),
        'result': [
            '2019-03-01 01:23:00+02:00',
            '2019-04-01 01:23:00+03:00',
            '2019-05-01 01:23:00+03:00',
        ]
    },

    '3 days': {
        'rule': rr('2019 05 1-3 1 23'),
        'start': parse_datetime('2019-01-01 00:00 EET'),
        'result': [
            '2019-05-01 01:23:00+03:00',
            '2019-05-02 01:23:00+03:00',
            '2019-05-03 01:23:00+03:00',
        ]
    },

    '3 weekdays': {
        'rule': rr('2019 05 * 1 23', weekdays='0-2'),
        'start': parse_datetime('2019-01-01 00:00 EET'),
        'result': [
            '2019-05-05 01:23:00+03:00',
            '2019-05-06 01:23:00+03:00',
            '2019-05-07 01:23:00+03:00',
            '2019-05-12 01:23:00+03:00',
            '2019-05-13 01:23:00+03:00',
            '2019-05-14 01:23:00+03:00',
            '2019-05-19 01:23:00+03:00',
            '2019-05-20 01:23:00+03:00',
            '2019-05-21 01:23:00+03:00',
            '2019-05-26 01:23:00+03:00',
            '2019-05-27 01:23:00+03:00',
            '2019-05-28 01:23:00+03:00',
        ]
    },

    '3 hours': {
        'rule': rr('2019 05 05 12-14 23'),
        'start': parse_datetime('2019-01-01 00:00 EET'),
        'result': [
            '2019-05-05 12:23:00+03:00',
            '2019-05-05 13:23:00+03:00',
            '2019-05-05 14:23:00+03:00',
        ]
    },

    '3 minutes': {
        'rule': rr('2019 05 01 1 21-23'),
        'start': parse_datetime('2019-01-01 00:00 EET'),
        'result': [
            '2019-05-01 01:21:00+03:00',
            '2019-05-01 01:22:00+03:00',
            '2019-05-01 01:23:00+03:00',
        ]
    },

    'start later': {
        'rule': rr('2000-2021 05 01 1 23'),
        'start': parse_datetime('2020-06-01 00:00 EET'),
        'result': [
            '2021-05-01 01:23:00+03:00',
        ]
    },

    'DST end, Daily+Hourly: Ambiguous as both': {
        'rule': rr('2019 10 26-28 2-4 */30'),
        'start': parse_datetime('2019-10-25 00:00 EET'),
        'result': [
            '2019-10-26 02:00:00+03:00',  # 25th 23:00 UTC
            '2019-10-26 02:30:00+03:00',  # 25th 23:30 UTC
            '2019-10-26 03:00:00+03:00',  # 26th 00:00 UTC
            '2019-10-26 03:30:00+03:00',  # 26th 00:30 UTC
            '2019-10-26 04:00:00+03:00',  # 26th 01:00 UTC
            '2019-10-26 04:30:00+03:00',  # 26th 01:30 UTC

            '2019-10-27 02:00:00+03:00',  # 26th 23:00 UTC
            '2019-10-27 02:30:00+03:00',  # 26th 23:30 UTC
            '2019-10-27 03:00:00+03:00',  # 27th 00:00 UTC *
            '2019-10-27 03:30:00+03:00',  # 27th 00:30 UTC *
            '2019-10-27 03:00:00+02:00',  # 27th 01:00 UTC *
            '2019-10-27 03:30:00+02:00',  # 27th 01:30 UTC *
            '2019-10-27 04:00:00+02:00',  # 27th 02:00 UTC
            '2019-10-27 04:30:00+02:00',  # 27th 02:30 UTC

            '2019-10-28 02:00:00+02:00',  # 28th 00:00 UTC
            '2019-10-28 02:30:00+02:00',  # 28th 00:30 UTC
            '2019-10-28 03:00:00+02:00',  # 28th 01:00 UTC
            '2019-10-28 03:30:00+02:00',  # 28th 01:30 UTC
            '2019-10-28 04:00:00+02:00',  # 28th 02:00 UTC
            '2019-10-28 04:30:00+02:00',  # 28th 02:30 UTC
        ]
    },
    'DST end, Daily: Ambiguous as DST ON': {
        'rule': rr('2019 10 26-28 3 30'),
        'start': parse_datetime('2019-10-25 00:00 EET'),
        'result': [
            '2019-10-26 03:30:00+03:00',  # 0:30 UTC
            '2019-10-27 03:30:00+03:00',  # 0:30 UTC
            '2019-10-28 03:30:00+02:00',  # 1:30 UTC
        ]
    },
    'DST end, Hourly: Ambiguous as both': {
        'rule': rr('2019 10 27 2-4 0,30'),
        'start': parse_datetime('2019-10-27 00:00 EET'),
        'result': [
            '2019-10-27 02:00:00+03:00',  # 23:00 UTC
            '2019-10-27 02:30:00+03:00',  # 23:30 UTC
            '2019-10-27 03:00:00+03:00',  # 00:00 UTC *
            '2019-10-27 03:30:00+03:00',  # 00:30 UTC *
            '2019-10-27 03:00:00+02:00',  # 01:00 UTC *
            '2019-10-27 03:30:00+02:00',  # 01:30 UTC *
            '2019-10-27 04:00:00+02:00',  # 02:00 UTC
            '2019-10-27 04:30:00+02:00',  # 02:30 UTC
        ]
    },

    'DST start, Daily+Hourly: No repetition': {
        'rule': rr('2018 03 24-26 2-4 */30'),
        'start': parse_datetime('2018-03-20 00:00 EET'),
        'result': [
            '2018-03-24 02:00:00+02:00',  # 00:00 UTC
            '2018-03-24 02:30:00+02:00',  # 00:30 UTC
            '2018-03-24 03:00:00+02:00',  # 01:00 UTC
            '2018-03-24 03:30:00+02:00',  # 01:30 UTC
            '2018-03-24 04:00:00+02:00',  # 02:00 UTC
            '2018-03-24 04:30:00+02:00',  # 02:30 UTC

            '2018-03-25 02:00:00+02:00',  # 00:00 UTC
            '2018-03-25 02:30:00+02:00',  # 00:30 UTC
            '2018-03-25 04:00:00+03:00',  # 01:00 UTC
            '2018-03-25 04:30:00+03:00',  # 01:30 UTC

            '2018-03-26 02:00:00+03:00',  # 23:00 UTC
            '2018-03-26 02:30:00+03:00',  # 23:30 UTC
            '2018-03-26 03:00:00+03:00',  # 00:00 UTC
            '2018-03-26 03:30:00+03:00',  # 00:30 UTC
            '2018-03-26 04:00:00+03:00',  # 01:00 UTC
            '2018-03-26 04:30:00+03:00',  # 01:30 UTC
        ]
    },
    'DST start, Daily: Non-existent as DST ON': {
        'rule': rr('2018 03 24-26 3 30'),
        'start': parse_datetime('2018-03-23 00:00 EET'),
        'result': [
            '2018-03-24 03:30:00+02:00',  # 1:30 UTC
            '2018-03-25 03:30:00+03:00',  # 0:30 UTC
            '2018-03-26 03:30:00+03:00',  # 0:30 UTC
        ]
    },
    'DST start, Hourly: No repetition': {
        'rule': rr('2019 03 31 2-5 0,30'),
        'start': parse_datetime('2019-03-31 00:00 EET'),
        'result': [
            '2019-03-31 02:00:00+02:00',  # 0:00 UTC
            '2019-03-31 02:30:00+02:00',  # 0:30 UTC
            '2019-03-31 04:00:00+03:00',  # 1:00 UTC
            '2019-03-31 04:30:00+03:00',  # 1:30 UTC
            '2019-03-31 05:00:00+03:00',  # 2:00 UTC
            '2019-03-31 05:30:00+03:00',  # 2:30 UTC
        ]
    },

    'DST starting at midnight: No repetition': {
        'rule': rr('2019 11 01-04 23,0,1 */30', tz='Brazil/East'),
        'start': parse_datetime('2019-01-01 00:00 Z'),
        'result': [
            '2019-11-01 00:00:00-03:00',  # 1st 3:00 UTC
            '2019-11-01 00:30:00-03:00',  # 1st 3:30 UTC
            '2019-11-01 01:00:00-03:00',  # 1st 4:00 UTC
            '2019-11-01 01:30:00-03:00',  # 1st 4:30 UTC

            '2019-11-01 23:00:00-03:00',  # 2nd 2:00 UTC
            '2019-11-01 23:30:00-03:00',  # 2nd 2:30 UTC
            '2019-11-02 00:00:00-03:00',  # 2nd 3:00 UTC
            '2019-11-02 00:30:00-03:00',  # 2nd 3:30 UTC
            '2019-11-02 01:00:00-03:00',  # 2nd 4:00 UTC
            '2019-11-02 01:30:00-03:00',  # 2nd 4:30 UTC

            '2019-11-02 23:00:00-03:00',  # 3rd 2:00 UTC
            '2019-11-02 23:30:00-03:00',  # 3rd 2:30 UTC
            '2019-11-03 01:00:00-02:00',  # 3rd 3:00 UTC
            '2019-11-03 01:30:00-02:00',  # 3rd 3:30 UTC

            '2019-11-03 23:00:00-02:00',  # 4th 1:00 UTC
            '2019-11-03 23:30:00-02:00',  # 4th 1:30 UTC
            '2019-11-04 00:00:00-02:00',  # 4th 2:00 UTC
            '2019-11-04 00:30:00-02:00',  # 4th 2:30 UTC
            '2019-11-04 01:00:00-02:00',  # 4th 3:00 UTC
            '2019-11-04 01:30:00-02:00',  # 4th 3:30 UTC

            '2019-11-04 23:00:00-02:00',  # 5th 1:00 UTC
            '2019-11-04 23:30:00-02:00',  # 5th 1:30 UTC
        ],
    },

    'DST starting at midnight, start from DST change': {
        'rule': rr('2019 11 01-03 23,0,1 */30', tz='Brazil/East'),
        'start': parse_datetime('2019-11-03 00:00:00-03:00'),
        'result': [
            '2019-11-03 01:00:00-02:00',  # 3rd 3:00 UTC
            '2019-11-03 01:30:00-02:00',  # 3rd 3:30 UTC
            '2019-11-03 23:00:00-02:00',  # 4th 1:00 UTC
            '2019-11-03 23:30:00-02:00',  # 4th 1:30 UTC
        ],
    },
}


@pytest.mark.parametrize('case', GET_NEXT_EVENTS_CASES.keys())
def test_get_next_events(case):
    data = GET_NEXT_EVENTS_CASES[case]

    result = list(get_next_events(data['rule'], data['start']))

    assert [str(x) for x in result] == data['result']


@pytest.mark.parametrize('rule,expected_count', [
    ('2019 * * 12 0', 365),
    ('2020 * * 12 0', 366),
    ('2020 * *  0 0', 366),
    ('2021 * * 12 0', 365),
    ('2021 * *  0 0', 365),
    ('2021-2030 * *  0 0', 3652),
])
def test_get_next_events_count(rule, expected_count):
    start = parse_datetime('1970-01-01 00:00 UTC')

    result = list(get_next_events(rr(rule), start))

    assert len(result) == expected_count


def test_get_next_events_iterating():
    start = parse_datetime('2020-01-01 00:00 EET')

    iterator = iter(get_next_events(rr('* * 12 45'), start))

    assert next(iterator) == start + timedelta(days=0, hours=12, minutes=45)
    assert next(iterator) == start + timedelta(days=1, hours=12, minutes=45)
    assert next(iterator) == start + timedelta(days=2, hours=12, minutes=45)
