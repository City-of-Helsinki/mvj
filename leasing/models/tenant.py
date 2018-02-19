from django.db import models
from django.utils.translation import ugettext_lazy as _

from .mixins import AddressMixin, TimestampedModelMixin


class GenericTenant(TimestampedModelMixin, AddressMixin):
    """A tenant is any legal entity that can lease land.

    A tenant can be a billpayer and/or contact person to another tenant.
    Name in Finnish: Vuokralainen

    Attributes:
        first_name (CharField):
        last_name (CharField):
        is_billpayer (BooleanField): Is this the tenant contact person that pays the bills? Bills will probably have to
            be shared among other billpayers.
            Name in Finnish: Laskunsaaja
        is_contact (BooleanField): May this tenant be contacted about itself or its parent?
            Name in Finnish: Yhteyshenkilö
        start_date (DateField):
        end_date (DateField):
        email (CharField):
        phone (CharField):
        language (CharField):
        ssid (CharField):
        is_protected (BooleanField): For when only certain privileged users should be able to access this person.
        customer_id (CharField):
        sap_customer_number (CharField):
        comment (CharField):
    """

    first_name = models.CharField(
        verbose_name=_("First name"),
        max_length=255,
    )

    last_name = models.CharField(
        verbose_name=_("Last name"),
        max_length=255,
    )
    is_billpayer = models.BooleanField(
        verbose_name=_("Is billpayer"),
        default=False,
    )

    is_contact = models.BooleanField(
        verbose_name=_("Is contact"),
        default=False,
    )

    start_date = models.DateField(
        verbose_name=_("Start date"),
    )

    end_date = models.DateField(
        verbose_name=_("End date"),
    )

    email = models.CharField(
        verbose_name=_("Email"),
        max_length=255,
    )

    phone = models.CharField(
        verbose_name=_("Phone"),
        max_length=255,
    )

    language = models.CharField(
        verbose_name=_("Language"),
        max_length=255,
    )

    ssid = models.CharField(
        verbose_name=_("SSID"),
        max_length=255,
    )

    is_protected = models.BooleanField(
        verbose_name=_("Is protected"),
    )

    customer_id = models.CharField(
        verbose_name=_("Customer ID"),
        max_length=255,
    )

    sap_customer_number = models.CharField(
        verbose_name=_("SAP customer number"),
        max_length=255,
    )

    comment = models.CharField(
        verbose_name=_("Comment"),
        max_length=255,
    )

    class Meta:
        abstract = True


class MainTenant(GenericTenant):
    """The actual tenant.

    Attributes:
        shares_numerator (PositiveIntegerField): This is the number that you have on top.
            Basically, how many parts does this tenant own of the lease.
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


class SubTenant(GenericTenant):
    """An extra billpayer or contact person for the main tenant.

    This is basically a tenant that doesn't have all the same fields as a main tenant and can be assigned as being part
    of the main

    Attributes:
        main_tenant (ForeignKey): What main tenant does this belong to?
    """
    main_tenant = models.ForeignKey(
        MainTenant,
        verbose_name=_("Main tenant"),
        on_delete=models.CASCADE,
    )
