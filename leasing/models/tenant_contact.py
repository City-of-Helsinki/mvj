from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumField

from .contact import Contact
from .tenant import Tenant


class TenantContactType(Enum):
    tenant = 'V'
    billpayer = 'L'
    contact = 'Y'


class TenantContact(models.Model):
    type = EnumField(
        TenantContactType,
        max_length=1,
    )

    tenant = models.ForeignKey(
        Tenant,
        verbose_name=_("Tenant"),
        on_delete=models.CASCADE,
    )

    contact = models.ForeignKey(
        Contact,
        verbose_name=_("Tenant"),
        on_delete=models.CASCADE,
    )

    start_date = models.DateField(
        verbose_name=_("Start date"),
    )

    end_date = models.DateField(
        verbose_name=_("End date"),
        null=True,
    )
