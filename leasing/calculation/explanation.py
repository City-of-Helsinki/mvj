class ExplanationItem:
    def __init__(self, subject=None, date_ranges=None, amount=None):
        self.subject = subject
        self.sub_items = []
        self.date_ranges = date_ranges
        self.amount = amount

    def __str__(self):
        return "{} {} {} {}".format(
            self.subject,
            self.date_ranges,
            self.amount,
            "\nSub items:\n  " + "\n  ".join([str(item) for item in self.sub_items])
            if self.sub_items
            else "",
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
        explanation_item = ExplanationItem(
            subject=subject, date_ranges=date_ranges, amount=amount
        )

        return self.add_item(explanation_item, related_item=related_item)

    def __str__(self):
        return "\n".join([str(item) for item in self.items])
