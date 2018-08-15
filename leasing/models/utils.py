import datetime
from collections import OrderedDict, namedtuple
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from dateutil.relativedelta import relativedelta
from django.utils.translation import ugettext_lazy as _

from leasing.enums import IndexType, PeriodType


def int_floor(value, precision):
    return value // precision * precision


class IndexCalculation:
    def __init__(self, amount=None, index=None, index_type=None, precision=None, x_value=None, y_value=None):
        self.explanation_items = []
        self.amount = amount
        self.index = index
        self.index_type = index_type
        self.precision = precision
        self.x_value = x_value
        self.y_value = y_value

    def _add_ratio_explanation(self, ratio):
        ratio_explanation_item = ExplanationItem(subject={
            "subject_type": "ratio",
            "description": _("Ratio {ratio}").format(ratio=ratio),
        })
        self.explanation_items.append(ratio_explanation_item)

    def calculate_type_1_2_3_4(self, index_value, precision, base):
        ratio = Decimal(int_floor(index_value, precision) / base).quantize(Decimal('.01'))

        self._add_ratio_explanation(ratio)

        return ratio * self.amount

    def calculate_type_5_7(self, index_value, base):
        ratio = Decimal(index_value / base).quantize(Decimal('.01'))

        self._add_ratio_explanation(ratio)

        return ratio * self.amount

    def calculate_type_6(self, index_value, base):
        if index_value <= self.x_value:
            return self.calculate_type_6_v2(index_value, base)

        rounded_index = int_floor(index_value, 10)

        # Decimal.quantize(Decimal('.01'), rounding=ROUND_HALF_UP) is used to round to two decimals.
        # see https://docs.python.org/3/library/decimal.html
        if rounded_index < self.y_value:
            dividend = Decimal(self.x_value + (index_value - self.x_value) / 2).quantize(Decimal('.01'),
                                                                                         rounding=ROUND_HALF_UP)
            ratio = (dividend / 100).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)

            self._add_ratio_explanation(ratio)

            return ratio * self.amount
        else:
            dividend = Decimal(self.y_value - (self.y_value - self.x_value) / 2).quantize(Decimal('.01'),
                                                                                          rounding=ROUND_HALF_UP)
            ratio = (dividend / 100).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)

            self._add_ratio_explanation(ratio)

            new_base_rent = (ratio * self.amount).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)

            new_base_rent_explanation_item = ExplanationItem(subject={
                "subject_type": "new_base_rent",
                "description": _("New base rent"),
            }, amount=new_base_rent)
            self.explanation_items.append(new_base_rent_explanation_item)

            return new_base_rent * Decimal(rounded_index / self.y_value).quantize(Decimal('.01'),
                                                                                  rounding=ROUND_HALF_UP)

    def calculate_type_6_v2(self, index_value, base):
        ratio = Decimal(int_floor(index_value, 10) / base).quantize(Decimal('.01'))

        self._add_ratio_explanation(ratio)

        return ratio * self.amount

    def calculate(self):
        if self.index.__class__ and self.index.__class__.__name__ == 'Index':
            index_value = self.index.number
        else:
            index_value = self.index

        if self.index_type == IndexType.TYPE_1:
            assert self.precision
            return self.calculate_type_1_2_3_4(index_value, self.precision, 50620)

        elif self.index_type == IndexType.TYPE_2:
            assert self.precision
            return self.calculate_type_1_2_3_4(index_value, self.precision, 4661)

        elif self.index_type == IndexType.TYPE_3:
            return self.calculate_type_1_2_3_4(index_value, 10, 418)

        elif self.index_type == IndexType.TYPE_4:
            return self.calculate_type_1_2_3_4(index_value, 20, 418)

        elif self.index_type == IndexType.TYPE_5:
            return self.calculate_type_5_7(index_value, 392)

        elif self.index_type == IndexType.TYPE_6:
            if not self.x_value or not self.y_value:
                return self.calculate_type_6_v2(index_value, 100)

            return self.calculate_type_6(index_value, 100)

        elif self.index_type == IndexType.TYPE_7:
            return self.calculate_type_5_7(index_value, 100)

        else:
            raise NotImplementedError('Cannot calculate index adjusted value for index type {}'.format(self.index_type))


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


def split_date_range(date_range, count):
    # TODO: Split by full months or weeks if possible
    assert len(date_range) == 2
    assert isinstance(date_range[0], datetime.date)
    assert isinstance(date_range[1], datetime.date)
    assert date_range[0] < date_range[1]

    if count == 0:
        return []

    if count == 1:
        return [date_range]

    start_date = date_range[0]
    end_date = date_range[1]

    days_between = (end_date - start_date).days
    # TODO: error if can't split as many times as requested?
    if days_between < count:
        raise RuntimeError("Can't split date range {} - {} ({} days) into {} parts".format(
            start_date, end_date, days_between, count))

    days_per_period = days_between // count

    result = []
    current_start = start_date
    while current_start < end_date:
        split_end = current_start + relativedelta(days=days_per_period)

        if split_end > end_date:
            split_end = end_date

        result.append((current_start, split_end))
        current_start = split_end + relativedelta(days=1)

        if current_start == end_date:
            result[-1] = (result[-1][0], end_date)

    return result


def get_monthly_amount_by_period_type(amount, period_type):
    if period_type == PeriodType.PER_MONTH:
        return amount
    elif period_type == PeriodType.PER_YEAR:
        return amount / 12
    else:
        raise NotImplementedError('Cannot calculate monthly amount for PeriodType {}'.format(period_type))


class DayMonth(namedtuple('DayMonthBase', ['day', 'month'])):
    @classmethod
    def from_date(cls, date_instance):
        if not isinstance(date_instance, datetime.date):
            raise ValueError('date_instance should be an instance of datetime.date')

        return cls(day=date_instance.day, month=date_instance.month)

    @classmethod
    def from_datetime(cls, datetime_instance):
        if not isinstance(datetime_instance, datetime.datetime):
            raise ValueError('datetime_instance should be an instance of datetime.datetime')

        return cls.from_date(datetime.date(year=datetime_instance.year, day=datetime_instance.day,
                                           month=datetime_instance.month))

    def asdict(self):
        return OrderedDict(zip(self._fields, self))


class ExplanationItem:
    def __init__(self, subject=None, date_ranges=None, amount=None):
        self.subject = subject
        self.sub_items = []
        self.date_ranges = date_ranges
        self.amount = amount

    def __str__(self):
        return '{} {} {} {}'.format(
            self.subject,
            self.date_ranges,
            self.amount,
            '\nSub items:\n  ' + '\n  '.join([str(item) for item in self.sub_items]) if self.sub_items else ''
        )


class Explanation:
    def __init__(self):
        self.items = []

    def add_item(self, explanation_item, related_item=None):
        if related_item:
            related_item.sub_items.append(explanation_item)
        else:
            self.items.append(explanation_item)

        return explanation_item

    def add(self, subject=None, date_ranges=None, amount=None, related_item=None):
        explanation_item = ExplanationItem(subject=subject, date_ranges=date_ranges, amount=amount)

        return self.add_item(explanation_item, related_item=related_item)

    def __str__(self):
        return '\n'.join([str(item) for item in self.items])
