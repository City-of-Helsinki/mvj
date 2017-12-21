from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumField, EnumIntegerField

from leasing.models.lease import Lease
from leasing.models.misc import PhoneNumber

__all__ = (
    "ClientLanguage",
    "ClientType",
    "Client",
    "RoleType",
    "ClientRole",
)


class ClientLanguage(Enum):
    FINNISH = 1
    SWEDISH = 2

    class Labels:
        FINNISH = _("Finnish")
        SWEDISH = _("Swedish")


class ClientType(Enum):
    PERSON = 0
    COMPANY = 1
    CITY_UNIT = 2
    ASSOCIATION = 3
    OTHER = 4

    class Labels:
        PERSON = _("Person")
        COMPANY = _("Company")
        CITY_UNIT = _("City unit")
        ASSOCIATION = _("Association")
        OTHER = _("Other")


class Client(models.Model):

    legacy_id = models.PositiveIntegerField(
        verbose_name=_("ID in the legacy system"),
        null=True,
        blank=True,
        db_index=True,
    )

    name = models.CharField(
        verbose_name=_("Name"),
        max_length=255,
        blank=False,
    )

    address = models.CharField(
        verbose_name=_("Address"),
        max_length=255,
        blank=True,
    )

    postal_code = models.CharField(
        verbose_name=_("Postal code"),
        max_length=255,
        blank=True,
    )

    country = models.CharField(
        verbose_name=_("Country"),
        max_length=2,
        blank=True,
    )

    language = EnumIntegerField(
        ClientLanguage,
        verbose_name=_("Language"),
        null=True,
    )

    business_id = models.CharField(
        max_length=9,
        verbose_name=_("Business ID"),
        blank=True,
    )

    phone_numbers = models.ManyToManyField(
        PhoneNumber,
        verbose_name=_("Phone numbers"),
        blank=True,
    )

    fax_number = models.CharField(
        verbose_name=_("Fax number"),
        max_length=255,
        blank=True,
    )

    comment = models.CharField(
        max_length=255,
        verbose_name=_("Comment"),
        blank=True,
    )

    client_type = EnumIntegerField(
        ClientType,
        verbose_name=_("Client type"),
        null=True,
    )

    debt_collection = models.TextField(
        verbose_name=_("Debt collection"),
        blank=True,
    )

    partnership_code = models.CharField(
        max_length=4,
        verbose_name=_("Partnership code"),
        blank=True,
    )

    email = models.CharField(
        max_length=255,
        verbose_name=_("Email"),
        blank=True,
    )

    trade_register = models.CharField(
        max_length=7,
        verbose_name=_("Trade register"),
        blank=True,
    )

    ssid = models.CharField(
        max_length=11,
        verbose_name=_("SSID"),
        blank=True,
    )


class RoleType(Enum):
    PAYER = 'L'
    CONTACT = 'Y'
    LESSEE = 'V'


class ClientRole():

    role_type = EnumField(
        RoleType,
    )

    start_date = models.DateField(
        verbose_name=_("Start date"),
    )

    end_date = models.DateField(
        verbose_name=_("End date"),
        null=True,
        blank=True,
    )

    client = models.ForeignKey(
        Client,
    )

    lease = models.ForeignKey(
        Lease,
    )
