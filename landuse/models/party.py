from django.conf import settings
from django.db import models
from django_countries.fields import CountryField

from landuse.models.agreement import LandUseAgreement
from utils.mixins import TimeStampedModel


class PartyType(models.TextChoices):
    COMPANY = ("COMPANY", "Yritys")
    PERSON = ("PERSON", "Henkilö")


class AgreementPartyRole(models.TextChoices):
    LAND_OWNER = ("LAND_OWNER", "Maanomistaja")
    DEVELOPER = ("DEVELOPER", "Toteuttaja")


class PartyDetailsBase(TimeStampedModel):
    """
    Shared fields for a contract party and an invoice recipient.
    """

    # In Finnish: Asiakastyyppi
    party_type = models.CharField(blank=True, choices=PartyType, max_length=255)

    # In Finnish: Nimi
    name = models.CharField(blank=True)

    # In Finnish: Henkilötunnus
    national_identification_number = models.CharField(blank=True)

    # In Finnish: Y-tunnus
    business_id = models.CharField(blank=True)

    # In Finnish: Kieli
    language = models.CharField(
        blank=True,
        choices=settings.LANGUAGES,
        max_length=10,
    )

    # In Finnish: Katuosoite
    street_address = models.CharField(blank=True)

    # In Finnish: Postinumero
    postal_code = models.CharField(blank=True)

    # In Finnish: Postitoimipaikka
    city = models.CharField(blank=True)

    # In Finnish: Maa
    country = CountryField(blank=True)

    # In Finnish: c/o
    care_of = models.CharField(blank=True)

    # In Finnish: Puhelinnumero
    phone = models.CharField(blank=True)

    # In Finnish: Sähköposti
    email = models.EmailField(blank=True)

    # In Finnish: Huomautus
    note = models.TextField(blank=True)

    class Meta:
        abstract = True


class InvoiceRecipient(PartyDetailsBase):
    """
    In Finnish: Laskunsaaja
    """

    # Explicitly declare the type of the default manager for type checking purposes.
    # Django doesn't guarantee that the objects property exists when inheriting from Model.
    objects: models.Manager["InvoiceRecipient"]

    # In Finnish: Sopimusosapuoli
    agreement_party = models.OneToOneField(
        "AgreementParty",
        on_delete=models.CASCADE,
        related_name="+",
    )


class AgreementParty(PartyDetailsBase):
    """
    In Finnish: Sopimusosapuoli
    """

    # In Finnish: Rooli
    role = models.CharField(
        blank=True,
        choices=AgreementPartyRole,
        max_length=255,
    )

    # In Finnish: Maankäyttösopimus
    agreement = models.ForeignKey(
        LandUseAgreement,
        on_delete=models.CASCADE,
        related_name="parties",
    )

    def get_primary_invoice_recipient(self) -> "AgreementParty | InvoiceRecipient":
        """
        When invoice recipient exists, they are the primary recipient.
        When they don't exist, agreement party is the recipient.
        """
        try:
            return InvoiceRecipient.objects.get(agreement_party=self)
        except InvoiceRecipient.DoesNotExist:
            return self
        except InvoiceRecipient.MultipleObjectsReturned as error:
            # Multiple recipients should not exist
            raise error


class ContactPerson(TimeStampedModel):
    """
    In Finnish: Yhteyshenkilö/neuvottelija
    """

    # In Finnish: Sopimusosapuoli
    agreement_party = models.ForeignKey(
        AgreementParty,
        on_delete=models.CASCADE,
        related_name="contact_persons",
    )

    # In Finnish: Nimi
    name = models.CharField(blank=True)

    # In Finnish: Puhelinnumero
    phone = models.CharField(blank=True)

    # In Finnish: Sähköposti
    email = models.EmailField(blank=True)


class BillingDetails(TimeStampedModel):
    """
    In Finnish: Laskutustiedot
    """

    # In Finnish: Sopimusosapuoli
    agreement_party = models.OneToOneField(
        AgreementParty,
        on_delete=models.CASCADE,
        related_name="billing_details",
    )

    # In Finnish: Ovt-tunnus
    ovt_code = models.CharField(blank=True)

    # In Finnish: SAP-asiakasnumero
    sap_customer_number = models.CharField(blank=True)

    # In Finnish: Asiakkaan viite
    customer_reference = models.CharField(blank=True)
