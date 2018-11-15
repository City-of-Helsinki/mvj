import inspect
from datetime import date

import pytest

from leasing.models.utils import (
    combine_ranges, fix_amount_for_overlap, get_billing_periods_for_year, get_next_business_day,
    get_range_overlap_and_remainder, is_business_day, is_date_on_first_quarter, split_date_range,
    subtract_range_from_range, subtract_ranges_from_ranges)


@pytest.mark.parametrize("s1, e1, s2, e2, expected", [
    (
        date(year=2010, month=1, day=1), date(year=2010, month=12, day=31),
        date(year=2010, month=2, day=1), date(year=2010, month=7, day=31),
        [
            (date(2010, 2, 1), date(2010, 7, 31)),
            [
                (date(2010, 1, 1), date(2010, 1, 31)),
                (date(2010, 8, 1), date(2010, 12, 31))
            ]
        ]
    ),
    (
        date(year=2010, month=1, day=1), date(year=2010, month=12, day=31),
        date(year=2009, month=1, day=1), date(year=2010, month=7, day=31),
        [
            (date(2010, 1, 1), date(2010, 7, 31)),
            [
                (date(2010, 8, 1), date(2010, 12, 31))
            ]
        ]
    ),
    (
        date(year=2010, month=1, day=1), date(year=2010, month=12, day=31),
        date(year=2010, month=10, day=1), date(year=2011, month=12, day=31),
        [
            (date(2010, 10, 1), date(2010, 12, 31)),
            [
                (date(2010, 1, 1), date(2010, 9, 30))
            ]
        ]
    ),
    (
        date(year=2010, month=1, day=1), date(year=2010, month=12, day=31),
        date(year=2009, month=1, day=1), date(year=2011, month=12, day=31),
        [
            (date(2010, 1, 1), date(2010, 12, 31)),
            []
        ]
    ),
    (
        date(year=2010, month=1, day=1), date(year=2010, month=12, day=31),
        date(year=2010, month=1, day=1), date(year=2010, month=12, day=31),
        [
            (date(2010, 1, 1), date(2010, 12, 31)),
            []
        ]
    ),
    (
        date(year=2010, month=1, day=1), date(year=2010, month=12, day=31),
        date(year=2009, month=1, day=1), date(year=2009, month=1, day=31),
        [
            None,
            []
        ]
    ),
    (
        date(year=2010, month=1, day=1), date(year=2010, month=12, day=31),
        date(year=2011, month=1, day=1), date(year=2011, month=1, day=31),
        [
            None,
            []
        ]
    ),
    (
        date(year=2010, month=1, day=1), date(year=2010, month=12, day=31),
        None, date(year=2010, month=7, day=31),
        [
            (date(2010, 1, 1), date(2010, 7, 31)),
            [
                (date(2010, 8, 1), date(2010, 12, 31))
            ]
        ]
    ),
    (
        date(year=2010, month=1, day=1), date(year=2010, month=12, day=31),
        date(year=2010, month=7, day=1), None,
        [
            (date(2010, 7, 1), date(2010, 12, 31)),
            [
                (date(2010, 1, 1), date(2010, 6, 30))
            ]
        ]
    ),
])
def test_get_overlap(s1, e1, s2, e2, expected):
    assert get_range_overlap_and_remainder(s1, e1, s2, e2) == expected


@pytest.mark.parametrize("year, periods_per_year, expected", [
    (2017, 1, [
        (date(year=2017, month=1, day=1), date(year=2017, month=12, day=31)),
    ]),
    (2017, 2, [
        (date(year=2017, month=1, day=1), date(year=2017, month=6, day=30)),
        (date(year=2017, month=7, day=1), date(year=2017, month=12, day=31)),
    ]),
    (2017, 3, [
        (date(year=2017, month=1, day=1), date(year=2017, month=4, day=30)),
        (date(year=2017, month=5, day=1), date(year=2017, month=8, day=31)),
        (date(year=2017, month=9, day=1), date(year=2017, month=12, day=31)),
    ]),
    (2017, 4, [
        (date(year=2017, month=1, day=1), date(year=2017, month=3, day=31)),
        (date(year=2017, month=4, day=1), date(year=2017, month=6, day=30)),
        (date(year=2017, month=7, day=1), date(year=2017, month=9, day=30)),
        (date(year=2017, month=10, day=1), date(year=2017, month=12, day=31)),
    ]),
    (2017, 5, []),
    (2017, 6, [
        (date(year=2017, month=1, day=1), date(year=2017, month=2, day=28)),
        (date(year=2017, month=3, day=1), date(year=2017, month=4, day=30)),
        (date(year=2017, month=5, day=1), date(year=2017, month=6, day=30)),
        (date(year=2017, month=7, day=1), date(year=2017, month=8, day=31)),
        (date(year=2017, month=9, day=1), date(year=2017, month=10, day=31)),
        (date(year=2017, month=11, day=1), date(year=2017, month=12, day=31)),
    ]),
    (2017, 7, []),
    (2017, 8, []),
    (2017, 9, []),
    (2017, 10, []),
    (2017, 11, []),
    (2017, 12, [
        (date(year=2017, month=1, day=1), date(year=2017, month=1, day=31)),
        (date(year=2017, month=2, day=1), date(year=2017, month=2, day=28)),
        (date(year=2017, month=3, day=1), date(year=2017, month=3, day=31)),
        (date(year=2017, month=4, day=1), date(year=2017, month=4, day=30)),
        (date(year=2017, month=5, day=1), date(year=2017, month=5, day=31)),
        (date(year=2017, month=6, day=1), date(year=2017, month=6, day=30)),
        (date(year=2017, month=7, day=1), date(year=2017, month=7, day=31)),
        (date(year=2017, month=8, day=1), date(year=2017, month=8, day=31)),
        (date(year=2017, month=9, day=1), date(year=2017, month=9, day=30)),
        (date(year=2017, month=10, day=1), date(year=2017, month=10, day=31)),
        (date(year=2017, month=11, day=1), date(year=2017, month=11, day=30)),
        (date(year=2017, month=12, day=1), date(year=2017, month=12, day=31)),
    ]),
    (2017, 13, []),
])
def test_get_billing_periods(year, periods_per_year, expected):
    assert get_billing_periods_for_year(year, periods_per_year) == expected


@pytest.mark.parametrize("amount, overlap, remainder, expected", [
    (
        1200,
        (date(2017, 7, 1), date(2017, 12, 31)),
        [(date(2017, 1, 1), date(2017, 6, 30))],
        600
    ),
])
def test_fix_amount_for_overlap(amount, overlap, remainder, expected):
    assert fix_amount_for_overlap(amount, overlap, remainder) == expected


@pytest.mark.parametrize("range1, subtract_range, expected", [
    (
        (date(2017, 1, 1), date(2017, 12, 31)),
        (date(2017, 1, 1), date(2017, 6, 30)),
        [(date(2017, 7, 1), date(2017, 12, 31))],
    ),
    (
        (date(2017, 1, 1), date(2017, 12, 31)),
        (date(2016, 1, 1), date(2017, 6, 30)),
        [(date(2017, 7, 1), date(2017, 12, 31))],
    ),
    (
        (date(2017, 1, 1), date(2017, 12, 31)),
        (date(2017, 4, 1), date(2017, 6, 30)),
        [(date(2017, 1, 1), date(2017, 3, 31)), (date(2017, 7, 1), date(2017, 12, 31))],
    ),
    (
        (date(2017, 1, 1), date(2017, 12, 31)),
        (date(2017, 7, 1), date(2017, 12, 31)),
        [(date(2017, 1, 1), date(2017, 6, 30))],
    ),
    (
        (date(2017, 1, 1), date(2017, 12, 31)),
        (date(2017, 7, 1), date(2018, 12, 31)),
        [(date(2017, 1, 1), date(2017, 6, 30))],
    ),
    # Full
    (
        (date(2017, 1, 1), date(2017, 12, 31)),
        (date(2017, 1, 1), date(2017, 12, 31)),
        [],
    ),
    (
        (date(2017, 1, 1), date(2017, 12, 31)),
        (date(2016, 1, 1), date(2018, 1, 1)),
        [],
    ),
    (
        (date(2017, 1, 1), date(2017, 12, 31)),
        (date(2016, 5, 5), date(2018, 4, 3)),
        [],
    ),
    # No overlap
    (
        (date(2017, 1, 1), date(2017, 12, 31)),
        (date(2016, 1, 1), date(2016, 12, 31)),
        [(date(2017, 1, 1), date(2017, 12, 31))],
    ),
    (
        (date(2017, 1, 1), date(2017, 12, 31)),
        (date(2018, 1, 1), date(2018, 12, 31)),
        [(date(2017, 1, 1), date(2017, 12, 31))],
    ),
])
def test_subtract_range_from_range(range1, subtract_range, expected):
    assert subtract_range_from_range(range1, subtract_range) == expected


@pytest.mark.parametrize("ranges, subtract_ranges, expected", [
    (
        [(date(2017, 1, 1), date(2017, 12, 31))],
        [(date(2017, 1, 1), date(2017, 6, 30))],
        [(date(2017, 7, 1), date(2017, 12, 31))],
    ),
    (
        [(date(2017, 1, 1), date(2017, 12, 31))],
        [(date(2016, 1, 1), date(2017, 6, 30))],
        [(date(2017, 7, 1), date(2017, 12, 31))],
    ),
    (
        [(date(2017, 1, 1), date(2017, 12, 31))],
        [(date(2017, 4, 1), date(2017, 6, 30))],
        [(date(2017, 1, 1), date(2017, 3, 31)), (date(2017, 7, 1), date(2017, 12, 31))],
    ),
    (
        [(date(2017, 1, 1), date(2017, 12, 31))],
        [(date(2017, 7, 1), date(2017, 12, 31))],
        [(date(2017, 1, 1), date(2017, 6, 30))],
    ),
    (
        [(date(2017, 1, 1), date(2017, 12, 31))],
        [(date(2017, 7, 1), date(2018, 12, 31))],
        [(date(2017, 1, 1), date(2017, 6, 30))],
    ),
    # Full
    (
        [(date(2017, 1, 1), date(2017, 12, 31))],
        [(date(2017, 1, 1), date(2017, 12, 31))],
        [],
    ),
    (
        [(date(2017, 1, 1), date(2017, 12, 31))],
        [(date(2016, 1, 1), date(2018, 1, 1))],
        [],
    ),
    (
        [(date(2017, 1, 1), date(2017, 12, 31))],
        [(date(2016, 5, 5), date(2018, 4, 3))],
        [],
    ),
    # No overlap
    (
        [(date(2017, 1, 1), date(2017, 12, 31))],
        [(date(2016, 1, 1), date(2016, 12, 31))],
        [(date(2017, 1, 1), date(2017, 12, 31))],
    ),
    (
        [(date(2017, 1, 1), date(2017, 12, 31))],
        [(date(2018, 1, 1), date(2018, 12, 31))],
        [(date(2017, 1, 1), date(2017, 12, 31))],
    ),
    # Multiple ranges
    (
        [(date(2017, 1, 1), date(2017, 12, 31)), (date(2017, 7, 1), date(2017, 12, 31))],
        [(date(2017, 1, 1), date(2017, 12, 31))],
        [],
    ),
    (
        [(date(2017, 1, 1), date(2017, 6, 30)), (date(2017, 7, 1), date(2017, 12, 31))],
        [(date(2017, 1, 1), date(2017, 12, 31))],
        [],
    ),
    (
        [(date(2017, 1, 1), date(2017, 6, 30)), (date(2017, 7, 1), date(2017, 12, 31))],
        [(date(2017, 4, 1), date(2017, 9, 30))],
        [(date(2017, 1, 1), date(2017, 3, 31)), (date(2017, 10, 1), date(2017, 12, 31))],
    ),
    # Multiple subtract_ranges
    (
        [(date(2017, 1, 1), date(2017, 12, 31))],
        [(date(2017, 1, 1), date(2017, 3, 31)), (date(2017, 11, 1), date(2017, 12, 31))],
        [(date(2017, 4, 1), date(2017, 10, 31))],
    ),
    (
        [(date(2017, 1, 1), date(2017, 12, 31))],
        [
            (date(2017, 3, 1), date(2017, 3, 31)),
            (date(2017, 6, 1), date(2017, 6, 30)),
            (date(2017, 12, 1), date(2017, 12, 31))],
        [
            (date(2017, 1, 1), date(2017, 2, 28)),
            (date(2017, 4, 1), date(2017, 5, 31)),
            (date(2017, 7, 1), date(2017, 11, 30)),
        ],
    ),
])
def test_subtract_ranges_from_ranges(ranges, subtract_ranges, expected):
    assert subtract_ranges_from_ranges(ranges, subtract_ranges) == expected


@pytest.mark.parametrize("ranges, expected", [
    (
        [
            (date(2017, 1, 1), date(2017, 6, 30)),
            (date(2017, 7, 1), date(2017, 12, 31)),
        ],
        [(date(2017, 1, 1), date(2017, 12, 31))],
    ),
    (
        [
            (date(2017, 1, 1), date(2017, 4, 30)),
            (date(2017, 3, 1), date(2017, 8, 1)),
            (date(2017, 7, 1), date(2017, 12, 31)),
        ],
        [(date(2017, 1, 1), date(2017, 12, 31))],
    ),
    (
        [
            (date(2017, 1, 1), date(2017, 4, 30)),
            (date(2017, 5, 1), date(2017, 6, 30)),
            (date(2017, 8, 1), date(2017, 12, 31)),
        ],
        [
            (date(2017, 1, 1), date(2017, 6, 30)),
            (date(2017, 8, 1), date(2017, 12, 31)),
        ],
    ),
    (
        [
            (date(2017, 1, 1), date(2017, 12, 31)),
            (date(2017, 1, 1), date(2017, 12, 31)),
        ],
        [(date(2017, 1, 1), date(2017, 12, 31))],
    ),
    (
        [
            (date(2017, 7, 1), date(2017, 12, 31)),
            (date(2017, 1, 1), date(2017, 4, 30)),
        ],
        [
            (date(2017, 1, 1), date(2017, 4, 30)),
            (date(2017, 7, 1), date(2017, 12, 31)),
        ],
    ),
    (
        [
            (date(2017, 1, 1), date(2017, 6, 30)),
            (date(2017, 4, 1), date(2017, 8, 31)),
        ],
        [(date(2017, 1, 1), date(2017, 8, 31))],
    ),
])
def test_combine_ranges(ranges, expected):
    assert combine_ranges(ranges) == expected


@pytest.mark.parametrize("date_range, count, expected", [
    (
        (date(2018, 1, 1), date(2018, 2, 1)),
        0,
        [],
    ),
    (
        (date(2018, 1, 1), date(2018, 2, 1)),
        1,
        [(date(2018, 1, 1), date(2018, 2, 1))],
    ),
    (
        (date(2018, 1, 1), date(2018, 12, 31)),
        1,
        [(date(2018, 1, 1), date(2018, 12, 31))],
    ),
    (
        (date(2018, 1, 1), date(2018, 6, 30)),
        2,
        [(date(2018, 1, 1), date(2018, 4, 1)), (date(2018, 4, 2), date(2018, 6, 30))],
    ),
    (
        (date(2018, 1, 1), date(2018, 6, 30)),
        3,
        [
            (date(2018, 1, 1), date(2018, 3, 2)),
            (date(2018, 3, 3), date(2018, 5, 2)),
            (date(2018, 5, 3), date(2018, 6, 30))
        ],
    ),
    (
        (date(2018, 1, 1), date(2018, 1, 5)),
        2,
        [
            (date(2018, 1, 1), date(2018, 1, 3)),
            (date(2018, 1, 4), date(2018, 1, 5)),
        ],
    ),
    # split_date_range doesn't guarantee the count of splits. at least for now.
    (
        (date(2018, 1, 1), date(2018, 1, 5)),
        3,
        [
            (date(2018, 1, 1), date(2018, 1, 2)),
            (date(2018, 1, 3), date(2018, 1, 5)),
        ],
    ),
    (
        (date(2018, 1, 1), date(2018, 1, 5)),
        4,
        [
            (date(2018, 1, 1), date(2018, 1, 2)),
            (date(2018, 1, 3), date(2018, 1, 5)),
        ],
    ),
])
def test_split_date_range(date_range, count, expected):
    assert split_date_range(date_range, count) == expected


def test_split_date_range_too_big_count():
    date_range = (date(2018, 1, 1), date(2018, 1, 5))
    count = 6

    with pytest.raises(RuntimeError) as e:
        split_date_range(date_range, count)

    assert str(e.value) == "Can't split date range 2018-01-01 - 2018-01-05 (4 days) into 6 parts"


@pytest.mark.django_db
@pytest.mark.parametrize("the_day, expected", [
    (None, ValueError),
    ('', ValueError),
    (date, ValueError),
    (date(2015, 1, 1), False),
    (date(2015, 1, 6), False),
    (date(2016, 1, 1), False),
    (date(2016, 1, 6), False),
    (date(2017, 1, 1), False),
    (date(2017, 1, 2), True),
    (date(2017, 12, 25), False),
    (date(2018, 12, 25), False),
    (date(2019, 12, 5), True),
    (date(2019, 12, 6), False),
    (date(2020, 1, 1), False),
    (date(2020, 1, 6), False),
    (date(2020, 1, 7), True),
    (date(2021, 4, 2), False),
    (date(2021, 6, 30), True),
])
def test_is_business_day(the_day, expected):
    if inspect.isclass(expected) and issubclass(expected, Exception):
        with pytest.raises(expected):
            is_business_day(the_day)
    else:
        assert is_business_day(the_day) == expected


@pytest.mark.django_db
@pytest.mark.parametrize("the_day, expected", [
    (None, ValueError),
    ('', ValueError),
    (date, ValueError),
    (date(2015, 1, 5), date(2015, 1, 7)),
    (date(2016, 1, 5), date(2016, 1, 7)),
    (date(2017, 1, 1), date(2017, 1, 2)),
    (date(2017, 1, 2), date(2017, 1, 3)),
    (date(2017, 12, 25), date(2017, 12, 27)),
    (date(2018, 12, 25), date(2018, 12, 27)),
    (date(2019, 12, 5), date(2019, 12, 9)),
    (date(2019, 12, 6), date(2019, 12, 9)),
    (date(2020, 1, 1), date(2020, 1, 2)),
    (date(2020, 1, 5), date(2020, 1, 7)),
    (date(2020, 1, 7), date(2020, 1, 8)),
    (date(2021, 4, 2), date(2021, 4, 6)),
    (date(2021, 6, 30), date(2021, 7, 1)),
])
def test_get_next_business_day(the_day, expected):
    if inspect.isclass(expected) and issubclass(expected, Exception):
        with pytest.raises(expected):
            get_next_business_day(the_day)
    else:
        assert get_next_business_day(the_day) == expected


@pytest.mark.django_db
@pytest.mark.parametrize("the_day, expected", [
    (None, ValueError),
    ('', ValueError),
    (date, ValueError),
    (date(2015, 1, 1), True),
    (date(2015, 1, 5), True),
    (date(2017, 12, 25), False),
    (date(2018, 12, 31), False),
    (date(2020, 3, 31), True),
    (date(2020, 4, 1), False),
])
def test_is_date_on_first_quarter(the_day, expected):
    if inspect.isclass(expected) and issubclass(expected, Exception):
        with pytest.raises(expected):
            is_date_on_first_quarter(the_day)
    else:
        assert is_date_on_first_quarter(the_day) == expected
