from django.db import models

from landuse.models.agreement import LandUseAgreement
from utils.mixins import TimeStampedModel


class Decision(TimeStampedModel):
    """
    In Finnish: Päätös
    """

    class DecisionMaker(models.TextChoices):
        LAND_MANAGER = ("land_manager", "Tonttipäällikkö")
        URBAN_ENVIRONMENT_COMMITTEE = (
            "urban_environment_committee",
            "Kaupunkiympäristölautakunta",
        )
        CITY_BOARD = ("city_board", "Kaupunginhallitus")

    class DecisionType(models.TextChoices):
        EASEMENT_CONDITION_ADDITION = (
            "easement_condition_addition",
            "Rasite- ja/tai rasitteenluont.ehdon lis. (1 ehto)",
        )
        LAND_USE_AGREEMENT_APPROVAL = (
            "land_use_agreement_approval",
            "Maankäyttösopimuksen hyväksyntä",
        )

    # In Finnish: Maankäyttösopimus
    agreement = models.ForeignKey(
        LandUseAgreement,
        on_delete=models.CASCADE,
        related_name="decisions",
    )

    # In Finnish: Otsikko
    title = models.CharField(blank=True)

    # In Finnish: Päättäjä
    decision_maker = models.CharField(
        choices=DecisionMaker.choices,
        blank=True,
    )

    # In Finnish: Päätöspvm
    decision_date = models.DateField(null=True, blank=True)

    # In Finnish: Pykälä §
    section = models.PositiveIntegerField(null=True, blank=True)

    # In Finnish: Päätöksen tyyppi
    decision_type = models.CharField(
        choices=DecisionType.choices,
        blank=True,
    )

    # In Finnish: Diaarinumero
    diary_number = models.CharField(blank=True)

    # In Finnish: Huomautus
    note = models.TextField(blank=True)


class DecisionCondition(TimeStampedModel):
    """
    In Finnish: Päätöksen ehto
    """

    class ConditionType(models.TextChoices):
        EASEMENT_OR_EASEMENT_LIKE_CONDITION = (
            "easement_or_easement_like_condition",
            "Rasite ja/tai rasitteenluonteinen ehto",
        )
        OTHER = ("other", "Muu ehto")

    # In Finnish: Päätös
    decision = models.ForeignKey(
        Decision,
        on_delete=models.CASCADE,
        related_name="conditions",
    )

    # In Finnish: Ehtotyyppi
    condition_type = models.CharField(
        choices=ConditionType.choices,
        blank=True,
    )

    # In Finnish: Valvontapäivämäärä
    supervision_date = models.DateField(null=True, blank=True)

    # In Finnish: Valvottu päivämäärä
    supervised_date = models.DateField(null=True, blank=True)

    # In Finnish: Huomautus
    note = models.TextField(blank=True)
