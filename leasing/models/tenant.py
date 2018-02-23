from django.db import models
from django.utils.translation import ugettext_lazy as _


class Tenant(models.Model):
    """The actual tenant.

    Attributes:
        shares_numerator (PositiveIntegerField): This is the number that you have on top.
            Basically, how many shares does this tenant own of the lease.
            Name in Finnish: Osuus murtolukuna
        shares_denominator (PositiveIntegerField): This is the number on the bottom that you divide the numerator with.
            Basically, how many shares are there in total.
            Name in Finnish: Osuus murtolukuna
        ovt_identifier (CharField):
        partner_code (CharField):
        reference (CharField):
    """

    shares_numerator = models.PositiveIntegerField(
        verbose_name=_("Numerator"),
    )

    shares_denominator = models.PositiveIntegerField(
        verbose_name=_("Denominator"),
    )

    ovt_identifier = models.CharField(
        verbose_name=_("OVT identifier"),
        max_length=255,
    )

    partner_code = models.CharField(
        verbose_name=_("Partner code"),
        max_length=255,
    )

    reference = models.CharField(
        verbose_name=_("Reference"),
        max_length=255,
    )
