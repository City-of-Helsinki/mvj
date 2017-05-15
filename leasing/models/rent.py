from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import RentType
from leasing.models import Lease
from leasing.models.mixins import TimestampedModelMixin


class Rent(TimestampedModelMixin):
    lease = models.ForeignKey(Lease, related_name="rents", on_delete=models.CASCADE)
    type = EnumField(RentType, verbose_name=_("Rent type"), max_length=255, default=RentType.FIXED)
    use = models.CharField(verbose_name=_("Use"), null=True, blank=True, max_length=2048)
    start_date = models.DateField(verbose_name=_("Effective start date"), null=True, blank=True)
    end_date = models.DateField(verbose_name=_("Effective end date"), null=True, blank=True)
    amount = models.DecimalField(verbose_name=_("Amount"), null=True, blank=True, max_digits=12,
                                 decimal_places=2, help_text=_("Per month if rent type is Fixed or Index."))

    def get_amount_for_period(self, period_start_date, period_end_date):
        if not self.amount or self.type in (RentType.FREE, RentType.MANUAL) or (
                (self.start_date and self.start_date > period_end_date) or
                (self.end_date and self.end_date < period_start_date)):
            return 0.0

        if self.type == RentType.ONE_TIME:
            return float(self.amount)

        start_date = period_start_date
        end_date = period_end_date

        if self.start_date and self.start_date > period_start_date:
            start_date = self.start_date

        if self.end_date and self.end_date < period_end_date:
            end_date = self.end_date

        # TODO: This calculation is only for demonstration
        return round((end_date - start_date).days / 30) * float(self.amount)
