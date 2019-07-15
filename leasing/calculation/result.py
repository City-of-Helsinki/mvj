from decimal import Decimal

from leasing.calculation.explanation import Explanation, ExplanationItem


class CalculationNote:
    def __init__(self, type, description):
        self.type = type
        self.description = description

    def __str__(self):
        return str(self.description)


class CalculationAmount:
    def __init__(self, item, date_range_start, date_range_end, amount):
        self.item = item
        self.amount = amount
        self.date_range_start = date_range_start
        self.date_range_end = date_range_end
        self.sub_amounts = []
        self.notes = []

    def __str__(self):
        result = 'Item: {}\n'.format(self.item)
        result += 'Date range: {} - {}\n'.format(self.date_range_start, self.date_range_end)
        result += 'Intended use: {}\n'.format(self.item.intended_use)
        result += 'Amount: {}\n'.format(self.amount)
        result += 'Notes:\n'
        for note in self.notes:
            result += str(note) + '\n'
        result += 'Sub amounts:\n'
        for sub_amount in self.sub_amounts:
            result += ' ' + str(sub_amount).replace('\n', '\n ')

        return result

    def add_sub_amounts(self, amounts):
        if not amounts:
            return

        # TODO: check that intended uses match
        self.sub_amounts.extend(amounts)

    def add_note(self, note):
        self.notes.append(note)

    def get_total_amount(self, allow_negative=False):
        amounts = [self.amount]
        amounts.extend([sub_amount.get_total_amount(allow_negative=True) for sub_amount in self.sub_amounts])

        return sum(amounts) if allow_negative else max(Decimal(0), sum(amounts))

    def get_total_amounts_by_intended_uses(self, totals=None):
        if totals is None:
            totals = {}

        if self.item.intended_use not in totals:
            totals[self.item.intended_use] = self.amount
        else:
            totals[self.item.intended_use] += self.amount

        for sub_amount in self.sub_amounts:
            sub_amount.get_total_amounts_by_intended_uses(totals)

        return totals

    def get_all_amounts(self):
        amounts = [self]
        for amount in self.sub_amounts:
            amounts.extend(amount.get_all_amounts())

        return amounts

    def get_explanation(self):
        explanation_item = ExplanationItem()
        explanation_item.subject = self.item
        explanation_item.date_ranges = [(self.date_range_start, self.date_range_end)]
        explanation_item.amount = self.amount

        for note in self.notes:
            explanation_item.sub_items.append(ExplanationItem(subject={
                "type": note.type,
                "description": note.description
            }, date_ranges=None, amount=None))

        if self.sub_amounts:
            for amount in self.sub_amounts:
                explanation_item.sub_items.append(amount.get_explanation())

        return explanation_item


class CalculationResult:
    def __init__(self, date_range_start, date_range_end):
        self.date_range_start = date_range_start
        self.date_range_end = date_range_end
        self.amounts = []

    def __str__(self):
        result = 'Date range: {} - {}\n'.format(self.date_range_start, self.date_range_end)

        result += 'Amounts:\n'
        for amount in self.amounts:
            result += str(amount)

        return result

    def add_amount(self, amount):
        if not amount:
            return

        self.amounts.append(amount)

    def get_total_amount(self):
        total = sum([amount.get_total_amount() for amount in self.amounts])

        # sum([]) returns int(0), return Decimal(0) instead
        if not total:
            return Decimal(0)
        else:
            return total

    def combine(self, calculation_result):
        assert isinstance(calculation_result, CalculationResult)

        self.amounts.extend(calculation_result.amounts)

    def get_total_amounts_by_intended_uses(self):
        totals = {}
        for amount in self.amounts:
            amount.get_total_amounts_by_intended_uses(totals)

        return totals

    def get_all_amounts(self):
        amounts = []
        for amount in self.amounts:
            amounts.extend(amount.get_all_amounts())

        return amounts

    def get_explanation(self):
        explanation = Explanation()

        for amount in self.amounts:
            explanation.add_item(amount.get_explanation())

        explanation_item = ExplanationItem()
        explanation_item.subject = {
            "type": "total",
            "description": "Total"
        }
        explanation_item.date_ranges = [(self.date_range_start, self.date_range_end)]
        explanation_item.amount = self.get_total_amount()
        explanation.add_item(explanation_item)

        return explanation


class FixedInitialYearRentCalculationResult(CalculationResult):
    def __init__(self, date_range_start, date_range_end):
        super().__init__(date_range_start, date_range_end)

        self.applied_ranges = []
        self.remaining_ranges = []

    def is_range_fully_applied(self):
        return self.applied_ranges and not self.remaining_ranges
