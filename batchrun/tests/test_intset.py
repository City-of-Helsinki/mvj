import time
from decimal import Decimal

import pytest

from ..intset import IntegerSetSpecifier, _parse_spec_part


@pytest.mark.parametrize('spec', [
    '*', '1-2', '2-3', '1-9', '1', '2', '1,2,3', '1-1', '1-9/3', '*/42'])
def test_can_be_constructed_from_valid_spec(spec):
    IntegerSetSpecifier(spec, 1, 9)


@pytest.mark.parametrize('spec', [
    '', 'abc', ' ', '**'
    ' 1-2', '1-2 ', ' *', '* ', '1-*', '*1', '1*', '*,',
    '-1', '1-', '1,', ',1', '0.0', '1.5',
    '1-9/-2', '5/5'
])
def test_invalid_spec_raises(spec):
    with pytest.raises(ValueError) as excinfo:
        IntegerSetSpecifier(spec, 1, 9)
    assert str(excinfo.value) == 'Invalid spec'


def test_can_be_constructed_with_min_equals_max():
    IntegerSetSpecifier('*', 42, 42)


def test_min_larger_than_max_raises():
    with pytest.raises(ValueError) as excinfo:
        IntegerSetSpecifier('*', 2, 1)
    assert str(excinfo.value) == (
        'max_value should not be smaller than min_value')


def test_parse_spec_part_raises_on_invalid_spec_part():
    with pytest.raises(ValueError) as excinfo:
        _parse_spec_part('**', 1, 9)
    assert str(excinfo.value) == 'Invalid spec part: **'


@pytest.mark.parametrize('spec', ['2-1', '9-3', '9-3/2'])
def test_invalid_range_in_spec_raises(spec):
    with pytest.raises(ValueError) as excinfo:
        IntegerSetSpecifier(spec, 1, 9)
    assert str(excinfo.value) == 'Invalid value range in spec'


@pytest.mark.parametrize('spec', ['1-10', '0-3', '10-11', '0-9/3'])
def test_outside_values_in_spec_raises(spec):
    with pytest.raises(ValueError) as excinfo:
        IntegerSetSpecifier(spec, 1, 9)
    assert str(excinfo.value) == 'Values in spec not within value range'


def test_parameters_available_as_properties():
    instance = IntegerSetSpecifier('5-30/3', 2, 42)

    assert instance.min_value == 2
    assert instance.max_value == 42
    assert instance.spec == '5-30/3'


@pytest.mark.parametrize('spec,minval,maxval,expected', [
    ('*', 0, 9, True),
    ('0-9', 0, 9, True),
    ('1-9', 0, 9, False),
    ('0-8', 0, 9, False),
    ('1-5,5-9', 1, 9, True),
    ('1-5,6-9', 1, 9, True),
    ('1-5,7-9', 1, 9, False),
    ('1-5,6-8', 1, 9, False),
    ('2-5,6-9', 1, 9, False),
    ('1-5,6-6,7-9', 1, 9, True),
    ('1-5,6-6/6,7-9', 1, 9, True),
    ('1-999999999', 1, 999999999, True),
    ('2-999999999', 1, 999999999, False),
    ('1-999999998', 1, 999999999, False),
    ('*/2,*/3,*/5,*/7,*/11,*/13,*/17,*/19,*/23', 1, 999999999, False),
    ('1-999,*/2', 0, 999, True),
])
def test_is_total(spec, minval, maxval, expected):
    instance = IntegerSetSpecifier(spec, minval, maxval)

    result = instance.is_total()

    assert result == expected


@pytest.mark.parametrize('orig_spec,simplified_spec', [
    ('*', '*'),
    ('1,2,3,4,5', '1-5'),
    ('1-5,6-8,9-12', '1-12'),
    ('5-10,8-15', '5-15'),
    ('5-13,10-12', '5-13'),
    ('1-20/2,21-30/2', '1-30/2'),
    ('1-20/2,17-30/2', '1-30/2'),
    ('1-20/2,20-30/2', '1-20/2,20-30/2'),
    ('1-20/2,16-30/2', '1-20/2,16-30/2'),
    ('1-2,3-4,6-8/2,6-20/2,5-30/3', '1-4,6-20/2,5-30/3'),
    ('1-2,3-4,6-8/2,5-20/2,5-30/3', '1-4,5-20/2,6-8/2,5-30/3'),
])
def test_simplify(orig_spec, simplified_spec):
    orig = IntegerSetSpecifier(orig_spec, 0, 100)

    simplified = orig.simplify()

    assert simplified.spec == simplified_spec


SPECS_WITH_EXPECTED_VALUES = [
    # (spec, min_value, max_value, expected_values)
    ('1-10', 0, 100, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
    ('*', 1, 7, [1, 2, 3, 4, 5, 6, 7]),
    ('2-8/2,3-9/3', 0, 10, [2, 3, 4, 6, 8, 9]),
    ('0-10/2', 0, 10, [0, 2, 4, 6, 8, 10]),
    ('1-10/2', 0, 10, [1, 3, 5, 7, 9]),
    ('*/2', 0, 10, [0, 2, 4, 6, 8, 10]),
    ('*/2', 1, 10, [2, 4, 6, 8, 10]),
    ('*/2', 2, 10, [2, 4, 6, 8, 10]),
    ('*/2,*/3', 0, 10, [0, 2, 3, 4, 6, 8, 9, 10]),
    ('*/42', 1, 9, []),
    ('*/42', 80, 200, [84, 126, 168]),
]


@pytest.mark.parametrize(
    'spec,minval,maxval,expected_values', SPECS_WITH_EXPECTED_VALUES)
def test_iter_returns_correct_values(spec, minval, maxval, expected_values):
    instance = IntegerSetSpecifier(spec, minval, maxval)

    result = list(instance)

    assert result == expected_values


def test_iter_can_do_first_items_of_large_ranges_fast():
    start_time = time.process_time()
    instance = IntegerSetSpecifier('42-100000000/3', 0, 10**8)
    iterator = iter(instance)
    first_value = next(iterator)
    second_value = next(iterator)
    consumed_cpu_time = time.process_time() - start_time

    assert consumed_cpu_time <= 0.01  # seconds
    assert first_value == 42
    assert second_value == 45


@pytest.mark.parametrize(
    'spec,minval,maxval,expected_values', SPECS_WITH_EXPECTED_VALUES)
def test_len(spec, minval, maxval, expected_values):
    instance = IntegerSetSpecifier(spec, minval, maxval)
    expected_len = len(expected_values)

    result = len(instance)

    assert result == expected_len


@pytest.mark.parametrize(
    'spec,minval,maxval,expected_values', SPECS_WITH_EXPECTED_VALUES)
def test_bool(spec, minval, maxval, expected_values):
    """
    Test casting to boolean.

    IntegerSetSpecifier which contains no values should evaluate as
    False in boolean context.
    """
    instance = IntegerSetSpecifier(spec, minval, maxval)
    expected_bool = True if expected_values else False

    result = bool(instance)

    assert result == expected_bool


@pytest.mark.parametrize(
    'spec,minval,maxval,expected_values', SPECS_WITH_EXPECTED_VALUES)
def test_contains_works_as_expected(spec, minval, maxval, expected_values):
    instance = IntegerSetSpecifier(spec, minval, maxval)

    for value in range(minval, maxval + 1):
        if value in expected_values:
            assert value in instance
        else:
            assert value not in instance


@pytest.mark.parametrize('value,expected', [
    # not present
    (None, False),
    (-1, False),
    (1.5, False),
    (1j, False),
    ('0', False),
    ('zero', False),

    # present
    (0.0, True),
    (1.0, True),
    (1+0j, True),
    (Decimal(0), True),
    (Decimal('1.00'), True),
    (False, True),  # False coalesces os 0
    (True, True),  # True coalesces as 1
])
def test_contains_works_with_non_integer_values(value, expected):
    instance = IntegerSetSpecifier('*', 0, 100)

    result = (value in instance)

    assert result is expected


@pytest.mark.parametrize('a_spec,a_min,a_max,b_spec,b_min,b_max,expected', [
    ('*', 1, 9, '*', 1, 9, True),
    ('*', 1, 9, '1-9', 1, 9, False),
    ('*', 1, 9, '*', 0, 9, False),
    ('*', 1, 9, '*', 1, 8, False),
    ('5', 1, 9, '5', 1, 9, True),
    ('5', 1, 9, '5-5', 1, 9, False),
    ('5', 1, 9, '5', 0, 9, False),
    ('5', 1, 9, '5', 1, 8, False),
    ('1,2,3', 1, 3, '1-3', 1, 3, False),
    ('1-1', 1, 9, '1', 1, 9, False),
    ('*/2', 1, 9, '*/3', 1, 9, False),
    ('*/100', 1, 9, '*/1000', 1, 9, False),
    ('123,456,7-10', 1, 999, '123,456,7-10', 1, 999, True),
    ('123,456,7-10', 1, 999, '7-10,123,456', 1, 999, False),
])
def test_eq(a_spec, a_min, a_max, b_spec, b_min, b_max, expected):
    a = IntegerSetSpecifier(a_spec, a_min, a_max)
    b = IntegerSetSpecifier(b_spec, b_min, b_max)

    result = (a == b)

    assert result is expected


def test_repr():
    instance = IntegerSetSpecifier('5-30/3', 2, 42)

    assert repr(instance) == "IntegerSetSpecifier('5-30/3', 2, 42)"
