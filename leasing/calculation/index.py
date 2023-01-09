from decimal import ROUND_HALF_UP, Decimal

from django.utils.translation import ugettext_lazy as _

from leasing.calculation.result import CalculationNote
from leasing.enums import IndexType

from .explanation import ExplanationItem


def int_floor(value, precision):
    return value // precision * precision


class LegacyIndexCalculation:
    def __init__(
        self,
        amount=None,
        index=None,
        index_type=None,
        precision=None,
        x_value=None,
        y_value=None,
    ):
        self.explanation_items = []
        self.notes = []
        self.amount = amount
        self.index = index
        self.index_type = index_type
        self.precision = precision
        self.x_value = x_value
        self.y_value = y_value

    def _add_ratio_explanation(self, ratio):
        ratio_explanation_item = ExplanationItem(
            subject={
                "subject_type": "ratio",
                "description": _("Ratio {ratio}").format(ratio=ratio),
            }
        )
        self.explanation_items.append(ratio_explanation_item)
        self.notes.append(
            CalculationNote(type="ratio", description=_("Ratio {}".format(ratio)))
        )

    def calculate_type_1_2_3_4(self, index_value, precision, base):
        ratio = Decimal(int_floor(index_value, precision) / base).quantize(
            Decimal(".01")
        )

        self._add_ratio_explanation(ratio)

        return ratio * self.amount

    def calculate_type_5_7(self, index_value, base):
        ratio = Decimal(index_value / base).quantize(Decimal(".01"))

        self._add_ratio_explanation(ratio)

        return ratio * self.amount

    def calculate_type_6(self, index_value, base):
        if index_value <= self.x_value:
            return self.calculate_type_6_v2(index_value, base)

        rounded_index = int_floor(index_value, 10)

        # Decimal.quantize(Decimal('.01'), rounding=ROUND_HALF_UP) is used to round to two decimals.
        # see https://docs.python.org/3/library/decimal.html
        if rounded_index < self.y_value:
            dividend = Decimal(
                self.x_value + (index_value - self.x_value) / 2
            ).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
            ratio = (dividend / 100).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)

            self._add_ratio_explanation(ratio)

            return ratio * self.amount
        else:
            dividend = Decimal(
                self.y_value - (self.y_value - self.x_value) / 2
            ).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
            ratio = (dividend / 100).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)

            self._add_ratio_explanation(ratio)

            new_base_rent = (ratio * self.amount).quantize(
                Decimal(".01"), rounding=ROUND_HALF_UP
            )

            new_base_rent_explanation_item = ExplanationItem(
                subject={
                    "subject_type": "new_base_rent",
                    "description": _("New base rent"),
                },
                amount=new_base_rent,
            )
            self.explanation_items.append(new_base_rent_explanation_item)

            self.notes.append(
                CalculationNote(
                    type="new_base_rent",
                    description=_("New base rent {}".format(new_base_rent)),
                )
            )

            y_ratio = Decimal(Decimal(rounded_index) / Decimal(self.y_value)).quantize(
                Decimal(".01"), rounding=ROUND_HALF_UP
            )

            # TODO: Different name for this ratio
            self._add_ratio_explanation(y_ratio)

            return new_base_rent * y_ratio

    def calculate_type_6_v2(self, index_value, base):
        ratio = Decimal(int_floor(index_value, 10) / base).quantize(Decimal(".01"))

        self._add_ratio_explanation(ratio)

        return ratio * self.amount

    def get_index_value(self):
        # TODO: error check
        if self.index.__class__ and self.index.__class__.__name__ == "Index":
            if self.index_type == IndexType.TYPE_1:
                from leasing.models.rent import LegacyIndex

                index_value = LegacyIndex.objects.get(index=self.index).number_1914
            elif self.index_type == IndexType.TYPE_2:
                from leasing.models.rent import LegacyIndex

                index_value = LegacyIndex.objects.get(index=self.index).number_1938
            else:
                index_value = self.index.number
        else:
            index_value = self.index

        return index_value

    def calculate(self):  # NOQA
        index_value = self.get_index_value()

        if self.index_type == IndexType.TYPE_1:
            precision = self.precision
            # TODO: precision is documented as 10%/20%, but we don't currently know which one we should use
            if not self.precision:
                precision = 20
            return self.calculate_type_1_2_3_4(index_value, precision, 50620)

        elif self.index_type == IndexType.TYPE_2:
            precision = self.precision
            # TODO: precision is documented as 10%/20%, but we don't currently know which one we should use
            if not self.precision:
                precision = 20
            return self.calculate_type_1_2_3_4(index_value, precision, 4661)

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
            raise NotImplementedError(
                "Cannot calculate index adjusted value for index type {}".format(
                    self.index_type
                )
            )
