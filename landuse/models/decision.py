from django.db import models

from landuse.models.agreement import LandUseAgreement


class Decision(models.Model):
    """
    In Finnish: Päätös
    """

    class DecisionMaker(models.TextChoices):
        LAND_MANAGER = ("LAND_MANAGER", "Tonttipäällikkö")
        URBAN_ENVIRONMENT_COMMITTEE = (
            "URBAN_ENVIRONMENT_COMMITTEE",
            "Kaupunkiympäristölautakunta",
        )
        CITY_BOARD = ("CITY_BOARD", "Kaupunginhallitus")

    class DecisionType(models.TextChoices):
        EASEMENT_CONDITION_ADDITION = (
            "EASEMENT_CONDITION_ADDITION",
            "Rasite- ja/tai rasitteenluont.ehdon lis. (1 ehto)",
        )
        LAND_USE_AGREEMENT_APPROVAL = (
            "LAND_USE_AGREEMENT_APPROVAL",
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


class DecisionCondition(models.Model):
    """
    In Finnish: Päätöksen ehto
    """

    class ConditionType(models.TextChoices):
        EASEMENT_OR_EASEMENT_LIKE_CONDITION = (
            "EASEMENT_OR_EASEMENT_LIKE_CONDITION",
            "Rasite ja/tai rasitteenluonteinen ehto",
        )
        OTHER = ("OTHER", "Muu ehto")

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
