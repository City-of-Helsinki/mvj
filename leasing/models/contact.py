from django.db import models
from django.utils.translation import ugettext_lazy as _

from .mixins import AddressMixin, TimestampedModelMixin


class Contact(TimestampedModelMixin, AddressMixin):
    """
    Attributes:
        first_name (CharField):
        last_name (CharField):
        email (CharField):
        phone (CharField):
        language (CharField):
        ssid (CharField):
        is_protected (BooleanField): For when only certain privileged users should be able to access this person.
        customer_id (CharField):
        sap_customer_number (CharField):
    """

    first_name = models.CharField(
        verbose_name=_("First name"),
        max_length=255,
    )

    last_name = models.CharField(
        verbose_name=_("Last name"),
        max_length=255,
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
