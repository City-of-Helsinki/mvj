from django.db import models
from django.utils.translation import ugettext_lazy as _

from leasing.models import Lease
from leasing.models.mixins import TimestampedModelMixin


class Rent(TimestampedModelMixin):
    lease = models.ForeignKey(Lease, related_name="rents", on_delete=models.CASCADE)
    rent_id = models.CharField(verbose_name=_("Rent id"), null=True, blank=True, max_length=255)
    use = models.CharField(verbose_name=_("Use"), null=True, blank=True, max_length=2048)
    quantity = models.FloatField(verbose_name=_("Quantity / Area"), null=True, blank=True)
    unit_price = models.DecimalField(verbose_name=_("Unit price"), null=True, blank=True, max_digits=12,
                                     decimal_places=2)
    rent_percent = models.IntegerField(verbose_name=_("Rent percent"), null=True, blank=True)
    discount = models.IntegerField(verbose_name=_("Discount"), null=True, blank=True)
    discount_start_date = models.DateField(verbose_name=_("Discount start date"), null=True, blank=True)
    discount_end_date = models.DateField(verbose_name=_("Discount end date"), null=True, blank=True)
    increase = models.IntegerField(verbose_name=_("Increase"), null=True, blank=True)
    increase_start_date = models.DateField(verbose_name=_("Increase start date"), null=True, blank=True)
    increase_end_date = models.DateField(verbose_name=_("Increase end date"), null=True, blank=True)
    index = models.CharField(verbose_name=_("Index"), null=True, blank=True, max_length=255)
