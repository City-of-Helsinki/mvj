from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from enumfields import EnumField

from field_permissions.registry import field_permissions
from leasing.validators import validate_business_id

from ..enums import LeaseholdTransferPartyType
from .mixins import NameModel, TimeStampedSafeDeleteModel


class LeaseholdTransferImportLog(TimeStampedSafeDeleteModel):
    """
    In Finnish: Vuokraoikeuden siirron tuontiloki
    """

    # In Finnish: Tiedoston nimi
    file_name = models.CharField(verbose_name=_("File name"), max_length=255)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Leasehold transfer import log")
        verbose_name_plural = pgettext_lazy(
            "Model name", "Leasehold transfer import logs"
        )

    def __str__(self):
        return self.file_name


class LeaseholdTransfer(TimeStampedSafeDeleteModel):
    """
    In Finnish: Vuokraoikeuden siirto
    """

    # In Finnish: Laitostunnus
    institution_identifier = models.CharField(
        verbose_name=_("Institution identifier"), max_length=127
    )

    # In Finnish: Ratkaisupäivämäärä
    decision_date = models.DateField(verbose_name=_("Decision date"))

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Leasehold transfer")
        verbose_name_plural = pgettext_lazy("Model name", "Leasehold transfers")

    def __str__(self):
        return self.institution_identifier


class LeaseholdTransferProperty(models.Model):
    """
    In Finnish: Vuokraoikeuden siirron kohde
    """

    # In Finnish: Tunnus
    identifier = models.CharField(verbose_name=_("Identifier"), max_length=127)

    transfer = models.ForeignKey(
        LeaseholdTransfer,
        verbose_name=_("Leasehold transfer"),
        on_delete=models.CASCADE,
        related_name="properties",
    )

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Leasehold transfer property")
        verbose_name_plural = pgettext_lazy(
            "Model name", "Leasehold transfer properties"
        )

    def __str__(self):
        return self.identifier


class LeaseholdTransferParty(NameModel):
    """
    In Finnish: Vuokraoikeuden siirron osapuoli
    """

    # In Finnish: Tyyppi
    type = EnumField(LeaseholdTransferPartyType)

    transfer = models.ForeignKey(
        LeaseholdTransfer,
        verbose_name=_("Leasehold transfer"),
        on_delete=models.CASCADE,
        related_name="parties",
    )

    # In Finnish: Y-tunnus
    business_id = models.CharField(
        verbose_name=_("Business ID"),
        max_length=255,
        null=True,
        blank=True,
        validators=[validate_business_id],
    )

    # In Finnish: Henkilötunnus
    national_identification_number = models.CharField(
        verbose_name=_("National identification number"),
        max_length=255,
        null=True,
        blank=True,
    )

    # In Finnish: Jaettava / Osoittaja
    share_numerator = models.PositiveIntegerField(
        verbose_name=_("Numerator"), null=True, blank=True
    )

    # In Finnish: Jakaja / Nimittäjä
    share_denominator = models.PositiveIntegerField(
        verbose_name=_("Denominator"), null=True, blank=True
    )

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Leasehold transfer party")
        verbose_name_plural = pgettext_lazy("Model name", "Leasehold transfer parties")
        ordering = ("-type",)

    def __str__(self):
        if self.share_numerator and self.share_denominator:
            return "{} {}/{}: {}".format(
                self.type, self.share_numerator, self.share_denominator, self.name
            )
        return "{}: {}".format(self.type, self.name)


field_permissions.register(LeaseholdTransfer)
field_permissions.register(LeaseholdTransferParty, exclude_fields=["transfer"])
