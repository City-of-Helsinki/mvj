from django.db import models
from django.utils.translation import ugettext_lazy as _

from leasing.models.mixins import TimestampedModelMixin


class Invoice(TimestampedModelMixin):
    tenant = models.ForeignKey('leasing.Tenant', related_name="invoices", on_delete=models.PROTECT)
    note = models.CharField(verbose_name=_("Note"), null=True, blank=True, max_length=2048)
    period_start_date = models.DateField(verbose_name=_("Period start date"), null=True, blank=True)
    period_end_date = models.DateField(verbose_name=_("Period end date"), null=True, blank=True)
    due_date = models.DateField(verbose_name=_("Due date"), null=True, blank=True)
    amount = models.DecimalField(verbose_name=_("Unit price"), max_digits=6, decimal_places=2)
