from auditlog.registry import auditlog
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from enumfields import EnumField

from field_permissions.registry import field_permissions
from leasing.enums import InfillDevelopmentCompensationState
from leasing.models.decision import DecisionMaker
from leasing.models.lease import IntendedUse
from users.models import User
from utils.models.fields import CustomFileField

from .mixins import TimeStampedSafeDeleteModel


class InfillDevelopmentCompensation(TimeStampedSafeDeleteModel):
    """
    In Finnish: Täydennysrakentamiskorvaus
    """

    # In Finnish: Nimi
    name = models.CharField(
        verbose_name=_("Name"), null=True, blank=True, max_length=255
    )

    # In Finnish: Diaarinumero
    reference_number = models.CharField(
        verbose_name=_("Reference number"), null=True, blank=True, max_length=255
    )

    # In Finnish: Asemakaavan nro.
    detailed_plan_identifier = models.CharField(
        verbose_name=_("Detailed plan identifier"),
        max_length=255,
        null=True,
        blank=True,
    )

    # In Finnish: Vastuuhenkilö
    user = models.ForeignKey(
        User, verbose_name=_("User"), related_name="+", on_delete=models.PROTECT
    )

    # In Finnish: Neuvotteluvaihe
    state = EnumField(
        InfillDevelopmentCompensationState,
        verbose_name=_("State"),
        null=True,
        blank=True,
        max_length=30,
    )

    # In Finnish: Vuokrasopimuksen muutospvm
    lease_contract_change_date = models.DateField(
        verbose_name=_("Lease contract change date"), null=True, blank=True
    )

    # In Finnish: Kommentti
    note = models.TextField(verbose_name=_("Note"), null=True, blank=True)

    leases = models.ManyToManyField(
        "leasing.Lease",
        through="leasing.InfillDevelopmentCompensationLease",
        related_name="leases",
    )

    # In Finnish: Alue
    geometry = models.MultiPolygonField(
        srid=4326, verbose_name=_("Geometry"), null=True, blank=True
    )

    recursive_get_related_skip_relations = ["user", "leases"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Infill development compensation")
        verbose_name_plural = pgettext_lazy(
            "Model name", "Infill development compensations"
        )

    def __str__(self):
        return (
            self.name
            if self.name
            else "InfillDevelopmentCompensation #{}".format(self.id)
        )


class InfillDevelopmentCompensationLease(TimeStampedSafeDeleteModel):
    """
    In Finnish: Täydennysrakentamiskorvausvuokraus
    """

    infill_development_compensation = models.ForeignKey(
        InfillDevelopmentCompensation,
        verbose_name=_("Infill development compensation"),
        related_name="infill_development_compensation_leases",
        on_delete=models.PROTECT,
    )

    lease = models.ForeignKey(
        "leasing.Lease",
        verbose_name=_("Lease"),
        related_name="infill_development_compensation_leases",
        on_delete=models.PROTECT,
    )

    # In Finnish: Kommentti
    note = models.TextField(verbose_name=_("Note"), null=True, blank=True)

    # In Finnish: Rahakorvaus
    monetary_compensation_amount = models.DecimalField(
        verbose_name=_("Monetary compensation amount"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: Korvausinvestointi
    compensation_investment_amount = models.DecimalField(
        verbose_name=_("Compensation investment amount"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: Arvon nousu
    increase_in_value = models.DecimalField(
        verbose_name=_("Increase in value"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: Osuus arvon noususta
    part_of_the_increase_in_value = models.DecimalField(
        verbose_name=_("Part of the increase in value"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: Vuokran alennus
    discount_in_rent = models.DecimalField(
        verbose_name=_("Discount in rent"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: Arvioitu maksuvuosi
    year = models.PositiveSmallIntegerField(
        verbose_name=_("Year"), null=True, blank=True
    )

    # In Finnish: Lähetetty SAP pvm
    sent_to_sap_date = models.DateField(
        verbose_name=_("Sent to SAP date"), null=True, blank=True
    )

    # In Finnish: Maksettu pvm
    paid_date = models.DateField(verbose_name=_("Paid date"), null=True, blank=True)

    recursive_get_related_skip_relations = ["infill_development_compensation", "lease"]

    class Meta:
        verbose_name = pgettext_lazy(
            "Model name", "Infill development compensation lease"
        )
        verbose_name_plural = pgettext_lazy(
            "Model name", "Infill development compensation leases"
        )


class InfillDevelopmentCompensationDecision(TimeStampedSafeDeleteModel):
    """
    In Finnish: Täydennysrakentamiskorvauspäätös
    """

    infill_development_compensation_lease = models.ForeignKey(
        InfillDevelopmentCompensationLease,
        verbose_name=_("Infill development compensation lease"),
        related_name="decisions",
        on_delete=models.PROTECT,
    )

    # In Finnish: Diaarinumero
    reference_number = models.CharField(
        verbose_name=_("Reference number"), null=True, blank=True, max_length=255
    )

    # In Finnish: Päättäjä
    decision_maker = models.ForeignKey(
        DecisionMaker,
        verbose_name=_("Decision maker"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Päätöspäivämäärä
    decision_date = models.DateField(
        verbose_name=_("Decision date"), null=True, blank=True
    )

    # In Finnish: Pykälä
    section = models.CharField(
        verbose_name=_("Section"), null=True, blank=True, max_length=255
    )

    recursive_get_related_skip_relations = ["infill_development_compensation_lease"]

    class Meta:
        verbose_name = pgettext_lazy(
            "Model name", "Infill development compensation decision"
        )
        verbose_name_plural = pgettext_lazy(
            "Model name", "Infill development compensation decisions"
        )


class InfillDevelopmentCompensationIntendedUse(TimeStampedSafeDeleteModel):
    """
    In Finnish: Täydennysrakentamiskorvauskäyttötarkoitus
    """

    infill_development_compensation_lease = models.ForeignKey(
        InfillDevelopmentCompensationLease,
        verbose_name=_("Infill development compensation lease"),
        related_name="intended_uses",
        on_delete=models.PROTECT,
    )

    intended_use = models.ForeignKey(
        IntendedUse,
        verbose_name=_("Intended use"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: K-m2
    floor_m2 = models.DecimalField(
        verbose_name=_("Floor m2"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: € / k-m2
    amount_per_floor_m2 = models.DecimalField(
        verbose_name=_("Amount per floor m^2"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    recursive_get_related_skip_relations = ["infill_development_compensation_lease"]

    class Meta:
        verbose_name = pgettext_lazy(
            "Model name", "Infill development compensation intended use"
        )
        verbose_name_plural = pgettext_lazy(
            "Model name", "Infill development compensation intended uses"
        )


def get_attachment_file_upload_to(instance, filename):
    return "/".join(
        [
            "idc_attachments",
            str(instance.infill_development_compensation_lease.id),
            filename,
        ]
    )


class InfillDevelopmentCompensationAttachment(TimeStampedSafeDeleteModel):
    """
    In Finnish: Täydennysrakentamiskorvausliitetiedosto
    """

    infill_development_compensation_lease = models.ForeignKey(
        InfillDevelopmentCompensationLease,
        verbose_name=_("Infill development compensation lease"),
        related_name="attachments",
        on_delete=models.PROTECT,
    )

    # In Finnish: Tiedosto
    file = CustomFileField(
        upload_to=get_attachment_file_upload_to, blank=False, null=False
    )

    # In Finnish: Lataaja
    uploader = models.ForeignKey(
        User, verbose_name=_("Uploader"), related_name="+", on_delete=models.PROTECT
    )

    # In Finnish: Latausaika
    uploaded_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Time uploaded")
    )

    recursive_get_related_skip_relations = [
        "infill_development_compensation_lease",
        "uploader",
    ]

    class Meta:
        verbose_name = pgettext_lazy(
            "Model name", "Infill development compensation attachment"
        )
        verbose_name_plural = pgettext_lazy(
            "Model name", "Infill development compensation attachments"
        )


auditlog.register(InfillDevelopmentCompensation)
auditlog.register(InfillDevelopmentCompensationLease)
auditlog.register(InfillDevelopmentCompensationDecision)
auditlog.register(InfillDevelopmentCompensationIntendedUse)
auditlog.register(InfillDevelopmentCompensationAttachment)

field_permissions.register(InfillDevelopmentCompensation, exclude_fields=[])
field_permissions.register(
    InfillDevelopmentCompensationLease,
    exclude_fields=["infill_development_compensation"],
)
field_permissions.register(
    InfillDevelopmentCompensationDecision,
    exclude_fields=["infill_development_compensation_lease"],
)
field_permissions.register(
    InfillDevelopmentCompensationIntendedUse,
    exclude_fields=["infill_development_compensation_lease"],
)
field_permissions.register(
    InfillDevelopmentCompensationAttachment,
    exclude_fields=["infill_development_compensation_lease"],
)
