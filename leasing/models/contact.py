from typing import TYPE_CHECKING

from auditlog.registry import auditlog
from django.conf.global_settings import LANGUAGES
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext, pgettext_lazy
from django_countries.fields import CountryField
from enumfields import EnumField

from field_permissions.registry import field_permissions
from leasing.enums import ContactType
from leasing.models.types import ContactsActiveLeases
from leasing.validators import validate_business_id

from .mixins import TimeStampedSafeDeleteModel

if TYPE_CHECKING:
    from leasing.models.tenant import Tenant


class Contact(TimeStampedSafeDeleteModel):
    """
    In Finnish: Yhteystieto
    """

    type = EnumField(ContactType, verbose_name=_("Type"), max_length=30)

    # In Finnish: Etunimi
    first_name = models.CharField(
        verbose_name=_("First name"), null=True, blank=True, max_length=255
    )

    # In Finnish: Sukunimi
    last_name = models.CharField(
        verbose_name=_("Last name"), null=True, blank=True, max_length=255
    )

    # In Finnish: (Yrityksen) Nimi
    name = models.CharField(
        verbose_name=_("Name"), null=True, blank=True, max_length=255
    )

    # In Finnish: c/o
    care_of = models.CharField(
        verbose_name=_("c/o"), null=True, blank=True, max_length=255
    )

    # In Finnish: Y-tunnus
    business_id = models.CharField(
        verbose_name=_("Business ID"),
        null=True,
        blank=True,
        max_length=255,
        validators=[validate_business_id],
    )

    # In Finnish: Osoite
    address = models.CharField(
        verbose_name=_("Address"), null=True, blank=True, max_length=255
    )

    # In Finnish: Postinumero
    postal_code = models.CharField(
        verbose_name=_("Postal code"), null=True, blank=True, max_length=255
    )

    # In Finnish: Kaupunki
    city = models.CharField(
        verbose_name=_("City"), null=True, blank=True, max_length=255
    )

    # In Finnish: Maa
    country = CountryField(verbose_name=_("Country"), null=True, blank=True)

    # In Finnish: Sähköpostiosoite
    email = models.CharField(
        verbose_name=_("Email"), null=True, blank=True, max_length=255
    )

    # In Finnish: Puhelinnumero
    phone = models.CharField(
        verbose_name=_("Phone"), null=True, blank=True, max_length=255
    )

    # In Finnish: Kieli
    language = models.CharField(
        verbose_name=_("Language"),
        choices=LANGUAGES,
        null=True,
        blank=True,
        max_length=255,
    )

    # In Finnish: Henkilötunnus
    national_identification_number = models.CharField(
        verbose_name=_("National identification number"),
        null=True,
        blank=True,
        max_length=255,
    )

    # In Finnish: Turvakielto
    address_protection = models.BooleanField(
        verbose_name=_("Address protection"), default=False
    )

    # In Finnish: SAP asiakasnumero
    sap_customer_number = models.CharField(
        verbose_name=_("SAP customer number"), null=True, blank=True, max_length=255
    )

    # In Finnish: Ovt-tunnus
    electronic_billing_address = models.CharField(
        verbose_name=_("Electronic billing address"),
        null=True,
        blank=True,
        max_length=255,
    )

    # In Finnish: Kumppanikoodi
    partner_code = models.CharField(
        verbose_name=_("Partner code"), null=True, blank=True, max_length=255
    )

    # In Finnish: Onko vuokranantaja
    is_lessor = models.BooleanField(verbose_name=_("Is a lessor"), default=False)

    # In Finnish: SAP myyntitoimisto
    sap_sales_office = models.CharField(
        verbose_name=_("SAP sales office"), null=True, blank=True, max_length=255
    )

    # In Finnish: Kommentti
    note = models.TextField(verbose_name=_("Note"), null=True, blank=True)

    # In Finnish: Palvelukokonaisuus
    service_unit = models.ForeignKey(
        "leasing.ServiceUnit",
        verbose_name=_("Service unit"),
        related_name="contacts",
        on_delete=models.PROTECT,
    )

    recursive_get_related_skip_relations = [
        "service_unit",
        "tenants",
        "tenantcontact",
        "litigants",
        "landuseagreementlitigantcontact",
        "credit_decisions",
    ]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Contact")
        verbose_name_plural = pgettext_lazy("Model name", "Contacts")
        ordering = ["type", "name", "last_name", "first_name"]
        permissions = [
            # Custom permission for a serializer method field `contacts_active_leases`,
            # required for being able to add field permissions for the field.
            ("view_contact_contacts_active_leases", "Can view contacts active leases"),
        ]

    def __str__(self):
        person_name = " ".join(
            [n for n in [self.first_name, self.last_name] if n]
        ).strip()

        if self.type == ContactType.PERSON:
            return person_name

        name = "{} ({})".format(self.name, self.type)

        if person_name:
            name = "{} {}".format(name, person_name)

        return name

    def get_name(self, anonymize_person=False):
        """
        Args:
            anonymize_person: If True, returns only the type of the contact,
                defaults to False.
        """
        if self.type == ContactType.PERSON:
            if anonymize_person:
                # Translators: Replaces the name of a person with a generic term.
                return pgettext("Replaces persons name", "PRIVATE")
            return " ".join([n for n in [self.first_name, self.last_name] if n]).strip()
        else:
            return self.name if self.name else ""

    def get_name_and_identifier(self):
        if self.type == ContactType.PERSON:
            name = " ".join([n for n in [self.first_name, self.last_name] if n]).strip()

            if self.national_identification_number:
                return _("{name} (National Identification Number {id})").format(
                    name=name, id=self.national_identification_number
                )
            else:
                return name
        else:
            name = self.name
            if self.business_id:
                return _("{name} (Business ID {id})").format(
                    name=name, id=self.business_id
                )
            else:
                return name

    def get_service_unit(self):
        return self.service_unit

    def get_contacts_active_leases(self):
        self.tenants: QuerySet[Tenant]
        now_date = timezone.now().date()
        active_leases = set()
        # Constructing the data in python way avoids N+1 queries when
        # related data is prefetched.
        for tenant in self.tenants.all():
            if tenant.lease.end_date is None or tenant.lease.end_date > now_date:
                active_leases.add(
                    (
                        tenant.lease.id,
                        tenant.lease.identifier.identifier,
                    )
                )
        active_leases_list: list[ContactsActiveLeases] = [
            {"lease_identifier": lease_identifier, "lease_id": lease_id}
            for lease_id, lease_identifier in active_leases
        ]
        return active_leases_list


auditlog.register(Contact)

field_permissions.register(
    Contact, exclude_fields=["lease", "invoice", "tenants", "tenantcontact"]
)
