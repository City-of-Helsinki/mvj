from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import InvoiceState
from leasing.models.mixins import TimestampedModelMixin


class Invoice(TimestampedModelMixin):
    tenants = models.ManyToManyField('leasing.Tenant')
    note = models.CharField(verbose_name=_("Note"), null=True, blank=True, max_length=2048)
    period_start_date = models.DateField(verbose_name=_("Period start date"), null=True, blank=True)
    period_end_date = models.DateField(verbose_name=_("Period end date"), null=True, blank=True)
    due_date = models.DateField(verbose_name=_("Due date"), null=True, blank=True)
    amount = models.DecimalField(verbose_name=_("Amount"), max_digits=6, decimal_places=2)
    reference_number = models.CharField(verbose_name=_("Reference number"), null=True, blank=True, max_length=2048)
    billing_contact = models.ForeignKey('leasing.Contact', related_name="invoice_billing_contacts", null=True,
                                        blank=True, on_delete=models.PROTECT)
    state = EnumField(InvoiceState, verbose_name=_("State"), max_length=255,
                      default=InvoiceState.PENDING)

    def create_reference_number(self):
        if not self.id:
            return None

        reference_number = '91112{}880'.format(self.id)

        self.reference_number = reference_number + str(
            (10 - (sum((7, 3, 1)[i % 3] * x for i, x in enumerate(map(int, str(reference_number)[::-1]))) % 10)) % 10)

        self.save()
