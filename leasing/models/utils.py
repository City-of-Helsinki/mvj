from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from leasing.enums import IndexType


def int_floor(value, precision):
    return value // precision * precision


def calculate_index_adjusted_value_type_1_2_3_4(value, index_value, precision, base):
    return int_floor(value, precision) / base * index_value


def calculate_index_adjusted_value_type_5_7(value, index_value, base):
    return value / base * index_value


def calculate_index_adjusted_value_type_6_v2(value, index_value):
    return int_floor(value, 10) * index_value


def calculate_index_adjusted_value(value, index_value, index_type=IndexType.TYPE_7, precision=None, **extra):
    if index_value.__class__ and index_value.__class__.__name__ == 'Index':
        index_value = index_value.number

    if index_type == IndexType.TYPE_1:
        assert precision
        return calculate_index_adjusted_value_type_1_2_3_4(value, index_value, precision, 50620)

    elif index_type == IndexType.TYPE_2:
        assert precision
        return calculate_index_adjusted_value_type_1_2_3_4(value, index_value, precision, 4661)

    elif index_type == IndexType.TYPE_3:
        return calculate_index_adjusted_value_type_1_2_3_4(value, index_value, 10, 418)

    elif index_type == IndexType.TYPE_4:
        return calculate_index_adjusted_value_type_1_2_3_4(value, index_value, 20, 418)

    elif index_type == IndexType.TYPE_5:
        return calculate_index_adjusted_value_type_5_7(value, index_value, 392)

    elif index_type == IndexType.TYPE_6 and extra:
        raise NotImplementedError('Cannot calculate index adjusted value for index type 6 version 1')

    elif index_type == IndexType.TYPE_6 and not extra:
        return calculate_index_adjusted_value_type_6_v2(value, index_value)

    elif index_type == IndexType.TYPE_7:
        return calculate_index_adjusted_value_type_5_7(value, index_value, 100)

    else:
        raise NotImplementedError('Cannot calculate index adjusted value for index type {}'.format(index_type))


def get_range_overlap(start1, end1, start2, end2):
    min_end = min(end1, end2) if end1 and end2 else end1 or end2
    max_start = max(start1, start2) if start1 and start2 else start1 or start2

    return max_start, min_end if max_start < min_end else None


def get_range_overlap_and_remainder(start1, end1, start2, end2):
    if start2 and end2 and ((start1 > start2 and start1 > end2) or end1 < start2):
        return [None, []]

    min_end = min(end1, end2) if end1 and end2 else end1 or end2
    max_start = max(start1, start2) if start1 and start2 else start1 or start2

    remainder = []
    if max_start == start1 and min_end == end1:
        remainder = []
    elif max_start > start1 and min_end < end1:
        remainder = [(start1, start2 - relativedelta(days=1)), (end2 + relativedelta(days=1), end1)]
    elif max_start == start1 and min_end <= end1:
        remainder = [(end2 + relativedelta(days=1), end1)]
    elif max_start == start2 and min_end >= end1:
        remainder = [(start1, start2 - relativedelta(days=1))]

    return [(max_start, min_end), remainder]


def get_last_date_of_month(year, month):
    return date(year=year, month=month, day=1) + relativedelta(day=31)


def get_spanned_months(start_date, end_date):
    months = 0
    start = date(start_date.year, start_date.month, 1)
    end = date(end_date.year, end_date.month, 1)
    while start <= end:
        months += 1
        start += relativedelta(months=1)
    return months


def get_date_range_amount_from_monthly_amount(monthly_amount, date_range_start, date_range_end,
                                              real_month_lengths=True):
    total = 0

    spanned_months = get_spanned_months(date_range_start, date_range_end)
    total += monthly_amount * spanned_months

    start_month_last_day = get_last_date_of_month(date_range_start.year, date_range_start.month)
    start_missing_days = date_range_start.day - 1

    if not real_month_lengths and start_missing_days in (14, 15, 16):
        start_missing_days = 15
    divisor = Decimal(start_month_last_day.day) if real_month_lengths else Decimal(30)
    total -= Decimal(start_missing_days) / divisor * monthly_amount

    end_month_last_day = get_last_date_of_month(date_range_end.year, date_range_end.month)
    end_missing_days = end_month_last_day.day - date_range_end.day

    if not real_month_lengths and end_missing_days in (14, 15, 16):
        end_missing_days = 15
    divisor = Decimal(end_month_last_day.day) if real_month_lengths else Decimal(30)
    total -= Decimal(end_missing_days) / divisor * monthly_amount

    return total


def fix_amount_for_overlap(amount, overlap, remainders):
    if not remainders:
        return amount

    overlap_delta = relativedelta(overlap[1] + relativedelta(days=1), overlap[0])
    overlap_months = overlap_delta.months

    if overlap_delta.days:
        # Round to a half month
        if overlap_delta.days in (14, 15, 16):
            overlap_months += Decimal(0.5)
        else:
            overlap_months += Decimal(overlap_delta.days / 30)

    remainder_months = 0
    for remainder in remainders:
        remainder_delta = relativedelta(remainder[1] + relativedelta(days=1), remainder[0])
        remainder_months += remainder_delta.months

        if remainder_delta.days:
            # Round to a half month
            if remainder_delta.days in (14, 15, 16):
                remainder_months += Decimal(0.5)
            else:
                remainder_months += Decimal(remainder_delta.days / 30)

    return amount / (overlap_months + remainder_months) * overlap_months


def get_billing_periods_for_year(year, periods_per_year):
    if periods_per_year < 1 or 12 % periods_per_year != 0 or periods_per_year > 12:
        # TODO: raise exception or log an error
        return []

    period_length = 12 // periods_per_year
    periods = []
    start = date(year=year, month=1, day=1)
    for i in range(periods_per_year):
        end = start + relativedelta(months=period_length) - relativedelta(days=1)
        periods.append((start, end))
        start = end + relativedelta(days=1)

    return periods


def combine_ranges(ranges):
    sorted_ranges = sorted(ranges)

    result = []

    new_range_start = None
    new_range_end = None

    for (range_start, range_end) in sorted_ranges:
        if new_range_start is None:
            new_range_start = range_start
            new_range_end = range_end
        elif new_range_end >= range_start or (range_start - new_range_end).days == 1:
            new_range_end = max(range_end, new_range_end)
        else:
            result.append((new_range_start, new_range_end))
            new_range_start = range_start
            new_range_end = range_end

    result.append((new_range_start, new_range_end))

    return result


def subtract_range_from_range(the_range, subtract_range):
    # TODO: check argument validity
    (range1_start, range1_end) = the_range
    (range2_start, range2_end) = subtract_range

    if range2_start > range1_end or range1_start > range2_end:
        return [(range1_start, range1_end)]

    result = []

    if range2_start > range1_start:
        result.append((range1_start, range2_start - relativedelta(days=1)))

    if range2_end < range1_end:
        result.append((range2_end + relativedelta(days=1), range1_end))

    return result


def subtract_ranges_from_ranges(ranges, subtract_ranges):
    # TODO: check argument validity
    combined_ranges = combine_ranges(ranges)
    combined_subtract_ranges = combine_ranges(subtract_ranges)

    i = 0
    while i < len(combined_ranges):
        for subtract_range in combined_subtract_ranges:
            result = subtract_range_from_range(combined_ranges[i], subtract_range)

            if not result:
                del combined_ranges[i]
                i -= 1
                break
            else:
                combined_ranges[i] = result[0]
                if len(result) > 1:
                    combined_ranges.insert(i + 1, result[1])
        i += 1

    return combined_ranges
