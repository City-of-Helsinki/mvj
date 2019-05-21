"""
Storing integer sets as a string specifier.

This module provides a class IntegerSetSpecifier which can be used to
store a set of positive integers within some range with a specifier
string.  The specifier string consists of comma separated parts which
could be single integers or ranges separated by dash, e.g "2,5,9-22,30".

Each part may also have a "step number" which is denoted by a slash and
a number, e.g. "2,10-30/5,99".  This step number means that only those
values within the range are included which are reachable by adding the
step number any number of times (including 0) to the first value within
the range, i.e. for a range "B-E/S" it contains each value v = B + n *
S, where n is an integer >= 0 and v <= E.

All included integer values are available by iterating the object:

    >>> list(IntegerSetSpecifier('*', 0, 6))
    [0, 1, 2, 3, 4, 5, 6]

    >>> list(IntegerSetSpecifier('2,4-6', 0, 6))
    [2, 4, 5, 6]

    >>> list(IntegerSetSpecifier('*/5', 0, 20))
    [0, 5, 10, 15, 20]

    >>> list(IntegerSetSpecifier('2-20/5', 0, 20))
    [2, 7, 12, 17]

    >>> list(IntegerSetSpecifier('10-15/2,1-5/2,3-15/3', 0, 2**28))
    [1, 3, 5, 6, 9, 10, 12, 14, 15]

Testing if a value is in the set can be done with the ``in`` operator:

    >>> 42 in IntegerSetSpecifier('30-50', 0, 100)
    True

    >>> 42 in IntegerSetSpecifier('43-100', 0, 100)
    False

    >>> 1234567 in IntegerSetSpecifier('*', 1, 123456789)
    True

It is also possible to check the number of values in the set with the
``len`` function:

    >>> len(IntegerSetSpecifier('1-10,31-35,50', 0, 100))
    16

    >>> len(IntegerSetSpecifier('*', 1, 123456789))
    123456789

    >>> len(IntegerSetSpecifier('2-10/2,3-10/3', 1, 10**9))
    7

Two integer set specifiers are considered equal if they have the same
specifier string and range:

    >>> (IntegerSetSpecifier('1-10', 0, 100) ==
    ...  IntegerSetSpecifier('1-10', 0, 100))
    True

    >>> (IntegerSetSpecifier('1-10', 0, 101) ==
    ...  IntegerSetSpecifier('1-10', 0, 100))
    False

    >>> (IntegerSetSpecifier('1,2,3,4,5,6,7,8,9,10', 0, 100) ==
    ...  IntegerSetSpecifier('1-10', 0, 100))
    False

It is also possible to simplify the specifier:

    >>> IntegerSetSpecifier('1-2,3-4,6-8/2,6-20/2,5-30/3', 1, 30).simplify()
    IntegerSetSpecifier('1-4,6-20/2,5-30/3', 1, 30)

    >>> IntegerSetSpecifier('1-2,3-4,6-8/2,5-20/2,5-30/3', 1, 30).simplify()
    IntegerSetSpecifier('1-4,5-20/2,6-8/2,5-30/3', 1, 30)
"""

import re
from itertools import chain
from typing import Any, Iterable, Iterator, List

_SPEC_PART_RX = r"""
    (\d+)                # a number
    |                    # or
    (?:                  # a range, which is
      (?:                #
        (?:\*)           #     a star
        |                #     or
        (?:(\d+)-(\d+))  #     number-number
      )                  #
      (?:/(\d+))?        #   optionally, followed by /number
    )
"""

_SPECIFIER_RX = re.compile(
    r'^(' + _SPEC_PART_RX + r')(,(' + _SPEC_PART_RX + r'))*$', re.VERBOSE)


class IntegerSetSpecifier:
    def __init__(self, spec: str, min_value: int, max_value: int) -> None:
        if not _SPECIFIER_RX.match(spec):
            raise ValueError('Invalid spec')
        if max_value < min_value:
            raise ValueError('max_value should not be smaller than min_value')

        self.spec: str = spec
        self.min_value: int = min_value
        self.max_value: int = max_value

        parsed_ranges = _parse_spec_as_ranges(spec, min_value, max_value)
        self._ranges: List[range] = _combine_ranges(parsed_ranges)
        self._separated: bool = _range_limits_are_separate(self._ranges)
        self._total_range: range = range(min_value, max_value + 1)

    def is_total(self) -> bool:
        if self.spec == '*' or self._ranges == [self._total_range]:
            return True
        elif self._separated:
            # There must be holes between the ranges, because otherwise
            # _combine_ranges would have combined all ranges to one.
            return False
        return all((x in self) for x in self._total_range)

    def simplify(self) -> 'IntegerSetSpecifier':
        def _format_range(rng: range) -> str:
            return (
                str(rng.start) if rng.start + rng.step >= rng.stop else
                '{}-{}{}'.format(
                    rng.start, rng.stop - 1,
                    '/{}'.format(rng.step) if rng.step != 1 else ''))
        simplified_spec = (
            '*' if self.is_total() else
            ','.join(_format_range(x) for x in self._ranges))
        return type(self)(simplified_spec, self.min_value, self.max_value)

    def __iter__(self) -> Iterator[int]:
        if self._separated:
            return iter(chain(*self._ranges))
        return self._iter_by_contains()

    def _iter_by_contains(self) -> Iterator[int]:
        min_start = min(x.start for x in self._ranges)
        max_stop = max(x.stop for x in self._ranges)
        for value in range(min_start, max_stop):
            if value in self:
                yield value

    def __len__(self) -> int:
        if self._separated:
            return sum(len(x) for x in self._ranges)
        return sum(1 for _ in self)

    def __contains__(self, value: Any) -> bool:
        return any(value in x for x in self._ranges)

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, type(self)) and
            self.spec == other.spec and
            self.min_value == other.min_value and
            self.max_value == other.max_value)

    def __repr__(self) -> str:
        return '{cls_name}({spec!r}, {min_value}, {max_value})'.format(
            cls_name=type(self).__name__,
            spec=self.spec,
            min_value=self.min_value,
            max_value=self.max_value,
        )


def _parse_spec_as_ranges(
        spec: str,
        min_value: int,
        max_value: int,
) -> List[range]:
    return [
        _parse_spec_part(part, min_value, max_value)
        for part in spec.split(',')
    ]


def _parse_spec_part(part: str, min_value: int, max_value: int) -> range:
    match = re.match(r'^(?:\*|(\d+)(?:-(\d+))?)(?:/(\d+))?$', part)
    if not match:
        raise ValueError('Invalid spec part: {}'.format(part))
    (start_str, stop_str, step_str) = match.groups()
    step = int(step_str) if step_str else 1
    if start_str and stop_str:
        (start, stop) = (int(start_str), int(stop_str))
        if start > stop:
            raise ValueError('Invalid value range in spec')
    elif start_str:
        start = stop = int(start_str)
    else:
        # It was a star: start from the smallest value that is dividable
        # by the step but larger or equal to min_value
        start = ((min_value - 1) // step + 1) * step
        stop = max_value
    if start < min_value or stop > max_value:
        raise ValueError('Values in spec not within value range')
    return range(start, stop + 1, step)


def _combine_ranges(ranges: Iterable[range]) -> List[range]:
    """
    Combine list of ranges to the most compact form.

    Simple ranges with step 1 can always be combined when their
    endpoints meet or overlap:

        >>> _combine_ranges([range(7, 10), range(1, 4),
        ...                  range(2, 6), range(3, 5)])
        [range(1, 6), range(7, 10)]
        >>> _combine_ranges([range(2, 7), range(3, 5)])
        [range(2, 7)]
        >>> _combine_ranges([range(1, 3), range(3, 5)])
        [range(1, 5)]
        >>> _combine_ranges([range(1, 3), range(4, 5)])
        [range(1, 3), range(4, 5)]
        >>> _combine_ranges([range(1, 2), range(2, 3), range(3, 4)])
        [range(1, 4)]

    If step is larger than 1, then combining can only occur when the
    ranges are in same "phase":

        >>> _combine_ranges([range(1, 8, 3), range(10, 14, 3)])
        [range(1, 14, 3)]
        >>> _combine_ranges([range(1, 8, 3), range(9, 14, 3)])
        [range(1, 8, 3), range(9, 14, 3)]

    Ranges with different step are not combined:

        >>> _combine_ranges([range(1, 8, 3), range(10, 14, 3),
        ...                  range(1, 20, 2)])
        [range(1, 20, 2), range(1, 14, 3)]

    Except if they have only a single item:

        >>> _combine_ranges([range(1, 3), range(3, 4, 3), range(4, 6)])
        [range(1, 6)]

    Empty ranges are removed:

        >>> _combine_ranges([range(1, 1), range(3, 4), range(6, 6)])
        [range(3, 4)]

    Empty input results in empty output:

        >>> _combine_ranges([])
        []
    """
    # Replace single item ranges with a range with step=1, remove
    # empty ranges and sort by step and start
    processed_ranges = sorted((
        x if len(x) != 1 else range(x.start, x.start + 1, 1)
        for x in ranges if x), key=(lambda x: (x.step, x.start, x.stop)))

    if not processed_ranges:
        return []

    result: List[range] = []
    last: range = processed_ranges[0]

    for cur in processed_ranges[1:]:
        # Enlarge the last range as long as the cur.start
        # is within it or in the edge (= within last_enlarded)
        last_enlarged = range(last.start, last.stop + last.step, last.step)
        if cur.step == last.step and cur.start in last_enlarged:
            last = range(last.start, max(last.stop, cur.stop), last.step)
        else:
            if last:
                result.append(last)
            last = cur

    if last:
        result.append(last)

    return result


def _range_limits_are_separate(ranges: Iterable[range]) -> bool:
    max_stop: int = 0
    for rng in sorted(ranges, key=(lambda x: (x.start, -x.stop))):
        if rng.start < max_stop:
            return False
        max_stop = max(rng.stop, max_stop)
    return True
