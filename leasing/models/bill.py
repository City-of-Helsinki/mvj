from django.db import models
from django.utils.translation import ugettext_lazy as _

from .mixins import NameModel


class BillType(NameModel):
    pass


class Bill(models.Model):
    bill_type = models.ForeignKey(
        BillType,
        verbose_name=_("Bill type"),
        on_delete=models.PROTECT,
    )

    capital_amount = models.DecimalField(
        verbose_name=_("Capital amount"),
        max_digits=10,
        decimal_places=2,
    )

    due_date = models.DateField(
        verbose_name=_("Due date"),
    )

    billing_period_start_date = models.DateField(
        verbose_name=_("Billing period start date"),
    )

    billing_period_end_date = models.DateField(
        verbose_name=_("Billing period end date"),
    )

    is_utter = models.BooleanField(
        verbose_name=_("Is utter"),
    )

    info = models.CharField(
        verbose_name=_("Info"),
        max_length=255,
    )
