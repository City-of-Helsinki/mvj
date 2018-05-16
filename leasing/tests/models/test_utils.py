from datetime import date

import pytest

from leasing.models.utils import (
    combine_ranges, fix_amount_for_overlap, get_billing_periods_for_year, get_range_overlap_and_remainder,
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
