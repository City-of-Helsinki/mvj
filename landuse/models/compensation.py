from django.db import models

from landuse.models.agreement import LandUseAgreement


class LandPolicyProgram(models.Model):
    """
    In Finnish: Maapoliittinen ohjelma
    """

    # In Finnish: Nimi
    name = models.CharField(blank=True)

    # In Finnish: Huojennusprosentin oletusarvo
    default_discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )


class LandUseCompensation(models.Model):
    """
    In Finnish: Maankäyttökorvauslaskelma
    """

    # In Finnish: Maankäyttösopimus
    agreement = models.OneToOneField(
        LandUseAgreement,
        on_delete=models.CASCADE,
        related_name="compensation",
    )

    # In Finnish: Excel-laskelman verkko-osoite
    excel_calculation_url = models.URLField(blank=True, null=True)

    # In Finnish: Rahakorvaus
    monetary_compensation = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # In Finnish: Maakorvaus
    land_compensation = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # In Finnish: Muu korvaus
    other_compensation = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # In Finnish: Yhteensä
    total_compensation = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # In Finnish: Perushinta
    base_price = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # In Finnish: Maakorvaus selite
    land_compensation_description = models.TextField(blank=True)

    # In Finnish: Muu selite
    other_compensation_description = models.TextField(blank=True)

    # In Finnish: Kaavaehdotusta edeltävä arvo
    value_before_detailed_plan_proposal = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # In Finnish: Purku tai muu vähennys
    demolition_or_other_deduction = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # In Finnish: Maankäyttökorvaus
    land_use_compensation = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # In Finnish: Maapoliittinen ohjelma
    land_policy_program = models.OneToOneField(
        LandPolicyProgram,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="compensations",
    )

    # In Finnish: Maapoliittinen huojennus %
    land_policy_program_discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # In Finnish: Neliöt
    public_areas_m2 = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # In Finnish: Hankinnan arvo (€)
    public_areas_acquisition_value = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
    )
