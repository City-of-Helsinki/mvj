from django.db import models

from landuse.models.agreement import LandUseAgreement
from utils.mixins import TimeStampedModel


class DetailedPlanSite(TimeStampedModel):
    """
    In Finnish: Kaava-alueen kohde
    """

    # In Finnish: Kohteen tunnus
    identifier = models.CharField(blank=True)

    # In Finnish: Kaava-alueen kohteen liittyvät maankäyttösopimukset
    # Note: specified in this model instead the other way around to avoid a circular import.
    agreements = models.ManyToManyField(
        LandUseAgreement, related_name="detailed_plan_sites"
    )


class SiteIntendedUse(TimeStampedModel):
    """
    In Finnish: Kaava-alueen kohteen käyttötarkoitus
    """

    # In Finnish: Käyttötarkoituksen nimi
    name = models.CharField(blank=False)


class SiteTenureType(TimeStampedModel):
    """
    In Finnish: Kaava-alueen kohteen hallintamuoto
    """

    # In Finnish: Hallintamuodon nimi
    name = models.CharField(blank=False)


class AgreementSite(TimeStampedModel):
    """
    In Finnish: Maankäyttösopimuksen kohde
    """

    class PreservationDesignation(models.TextChoices):
        """
        In Finnish: Asemakaavan suojelumerkintä
        """

        SR1 = ("SR1", "SR1")
        SR2 = ("SR2", "SR2")
        SR3 = ("SR3", "SR3")

    # In Finnish: Maankäyttösopimus
    agreement = models.ForeignKey(
        LandUseAgreement,
        on_delete=models.CASCADE,
        related_name="compensation_sites",
    )

    # In Finnish: Kohteen tunnus
    identifier = models.CharField(blank=True)

    # In Finnish: Pinta-ala (m²)
    area_m2 = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # In Finnish: Kerrosala (kem²)
    floor_area_kem2 = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # In Finnish: Käyttötarkoitus
    intended_use = models.ForeignKey(
        SiteIntendedUse,
        on_delete=models.PROTECT,
        related_name="agreement_sites",
        null=True,
    )

    # In Finnish: Hallintamuoto
    tenure_types = models.ManyToManyField(
        SiteTenureType,
        related_name="agreement_sites",
    )

    # In Finnish: Asemakaavan suojelumerkintä
    preservation_designation = models.CharField(
        choices=PreservationDesignation, null=True, blank=True
    )

    # In Finnish: Asumismuotovelvoite
    has_housing_obligation = models.BooleanField(default=False)

    # In Finnish: Yksikköhinta (€/kem²)
    unit_price_euro_per_kem2 = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
    )
