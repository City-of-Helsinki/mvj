from auditlog.registry import auditlog
from django.conf.global_settings import LANGUAGES
from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import ContactType

from .mixins import TimeStampedSafeDeleteModel


class Contact(TimeStampedSafeDeleteModel):
    """
    In Finnish: Yhteystieto
    """
    type = EnumField(ContactType, verbose_name=_("Type"), max_length=30)

    # In Finnish: Etunimi
    first_name = models.CharField(verbose_name=_("First name"), null=True, blank=True, max_length=255)

    # In Finnish: Sukunimi
    last_name = models.CharField(verbose_name=_("Last name"), null=True, blank=True, max_length=255)

    name = models.CharField(verbose_name=_("Name"), null=True, blank=True, max_length=255)

    # In Finnish: Y-tunnus
    business_id = models.CharField(verbose_name=_("Business ID"), null=True, blank=True, max_length=255)

    # In Finnish: Osoite
    address = models.CharField(verbose_name=_("Address"), null=True, blank=True, max_length=255)

    # In Finnish: Postinumero
    postal_code = models.CharField(verbose_name=_("Postal code"), null=True, blank=True, max_length=255)

    # In Finnish: Kaupunki
    city = models.CharField(verbose_name=_("City"), null=True, blank=True, max_length=255)

    # In Finnish: Sähköpostiosoite
    email = models.CharField(verbose_name=_("Email"), null=True, blank=True, max_length=255)

    # In Finnish: Puhelinnumero
    phone = models.CharField(verbose_name=_("Phone"), null=True, blank=True, max_length=255)

    # In Finnish: Kieli
    language = models.CharField(verbose_name=_("Language"), choices=LANGUAGES, null=True, blank=True, max_length=255)

    # In Finnish: Henkilötunnus
    national_identification_number = models.CharField(verbose_name=_("National identification number"),
                                                      null=True, blank=True, max_length=255)

    # In Finnish: Turvakielto
    address_protection = models.BooleanField(verbose_name=_("Address protection"), default=False)

    # In Finnish: Asiakasnumero
    customer_number = models.CharField(verbose_name=_("Customer number"), null=True, blank=True, max_length=255)

    # In Finnish: SAP asiakasnumero
    sap_customer_number = models.CharField(verbose_name=_("SAP customer number"), null=True, blank=True, max_length=255)

    # In Finnish: Ovt-tunnus
    electronic_billing_address = models.CharField(verbose_name=_("Electronic billing address"), null=True, blank=True,
                                                  max_length=255)

    # In Finnish: Kumppanikoodi
    partner_code = models.CharField(verbose_name=_("Partner code"), null=True, blank=True, max_length=255)

    # In Finnish: Onko vuokranantaja
    is_lessor = models.BooleanField(verbose_name=_("Is a lessor"), default=False)

    def __str__(self):
        person_name = ' '.join([n for n in [self.first_name, self.last_name] if n]).strip()

        if self.type == ContactType.PERSON:
            return person_name

        name = '{} ({})'.format(self.name, self.type)

        if person_name:
            name = '{} {}'.format(name, person_name)

        return name

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Contact")
        verbose_name_plural = pgettext_lazy("Model name", "Contacts")
        ordering = ['type', 'name', 'last_name', 'first_name']


auditlog.register(Contact)
