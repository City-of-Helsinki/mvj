from django.contrib.gis.db import models
from django.db import connection, transaction
from django.db.models import Max
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField
from sequences import get_next_value

from leasing.enums import (
    DueDatesPosition,
    InfillDevelopmentCompensationState,
    LandUseAgreementLitigantContactType,
    LandUseContractType,
)
from leasing.models.contact import Contact
from leasing.models.decision import DecisionMaker
from leasing.models.land_area import AbstractAddress
from leasing.models.lease import District, Municipality
from users.models import User

from .mixins import NameModel, TimeStampedSafeDeleteModel


class LandUseAgreementType(NameModel):
    """
    In Finnish: Laji
    """

    identifier = models.CharField(
        verbose_name=_("Identifier"), max_length=255, unique=True
    )
    sap_material_code = models.CharField(
        verbose_name=_("SAP material code"), null=True, blank=True, max_length=255
    )
    sap_order_item_number = models.CharField(
        verbose_name=_("SAP order item number"), null=True, blank=True, max_length=255
    )
    due_dates_position = EnumField(
        DueDatesPosition,
        verbose_name=_("Due dates position"),
        default=DueDatesPosition.START_OF_MONTH,
        max_length=30,
    )


class LandUseAgreementStatus(NameModel):
    """
    In Finnish: Olotila
    """


class LandUseAgreementDefinition(NameModel):
    """
    In Finnish: Määritelmä
    """


class LandUseAgreementIdentifier(TimeStampedSafeDeleteModel):
    """
    In Finnish: Vuokraustunnus
    """

    # In Finnish: Laji
    type = models.ForeignKey(
        LandUseAgreementType,
        verbose_name=_("Land use agreement type"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Kaupunki
    municipality = models.ForeignKey(
        Municipality,
        verbose_name=_("Municipality"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Kaupunginosa
    district = models.ForeignKey(
        District, verbose_name=_("District"), related_name="+", on_delete=models.PROTECT
    )

    # In Finnish: Juokseva numero
    sequence = models.PositiveIntegerField(verbose_name=_("Sequence number"))

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Lease identifier")
        verbose_name_plural = pgettext_lazy("Model name", "Lease identifiers")
        unique_together = ("type", "municipality", "district", "sequence")

    def __str__(self):
        """Returns the lease identifier as a string

        The Land use agreement identifier is constructed out of type, municipality,
        district, and sequence, in that order. For example, the identifier
        for a residence (A1) in Helsinki (1), Vallila (22), and sequence
        number 1 would be A1122-1.
        """
        return "{}{}{:02}-{}".format(
            self.type.identifier,
            self.municipality.identifier,
            int(self.district.identifier),
            self.sequence,
        )


class LandUseAgreementCompensations(NameModel):
    """
    In Finnish: Maankäyttökorvaus
    """

    cash_compensation = models.DecimalField(
        verbose_name=_("Cash compensation"), decimal_places=2, max_digits=12
    )
    land_compensation = models.DecimalField(
        verbose_name=_("Land compensation"), decimal_places=2, max_digits=12
    )

    other_compensation = models.DecimalField(
        verbose_name=_("Other compensation"), decimal_places=2, max_digits=12
    )
    first_installment_increase = models.DecimalField(
        verbose_name=_("First installment increase"), decimal_places=2, max_digits=12
    )

    street_acquisition_value = models.DecimalField(
        verbose_name=_("Street acquisition value"), decimal_places=2, max_digits=12
    )

    street_area = models.PositiveIntegerField()
    park_acquisition_value = models.DecimalField(
        verbose_name=_("Park acquisition value"), decimal_places=2, max_digits=12
    )

    park_area = models.PositiveIntegerField()
    other_acquisition_value = models.DecimalField(
        verbose_name=_("Other acquisition value"), decimal_places=2, max_digits=12
    )

    other_area = models.PositiveIntegerField()


class LandUseAgreement(TimeStampedSafeDeleteModel):
    """
    In Finnish: Maankäyttösopimus
    """

    # In Finnish: Tunnus
    identifier = models.OneToOneField(
        LandUseAgreementIdentifier,
        verbose_name=_("Land use agreement identifier"),
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Kaupunki
    municipality = models.ForeignKey(
        Municipality,
        verbose_name=_("Municipality"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Kaupunginosa
    district = models.ForeignKey(
        District, verbose_name=_("District"), related_name="+", on_delete=models.PROTECT
    )

    # In Finnish: Määritelmä
    definition = models.ForeignKey(
        LandUseAgreementDefinition,
        verbose_name=_("Land use agreement definition"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Olotila
    status = models.ForeignKey(
        LandUseAgreementStatus,
        verbose_name=_("Land use agreement status"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Laji
    type = models.ForeignKey(
        LandUseAgreementType,
        verbose_name=_("Land use agreement type"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Valmistelija
    preparer = models.ForeignKey(
        User,
        verbose_name=_("Preparer"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Sopimuksen tyyppi
    land_use_contract_type = EnumField(
        LandUseContractType,
        verbose_name=_("Contract type"),
        null=True,
        blank=True,
        max_length=30,
    )

    # In Finnish: Arvioitu toteutumisvuosi
    estimated_completion_year = models.PositiveSmallIntegerField(
        verbose_name=_("Estimated completion year"), null=True, blank=True
    )

    # In Finnish: Arvioitu esittelyvuosi
    estimated_introduction_year = models.PositiveSmallIntegerField(
        verbose_name=_("Estimated introduction year"), null=True, blank=True
    )

    # In Finnish: Hankealue
    project_area = models.CharField(
        verbose_name=_("Project area"), null=True, blank=True, max_length=255
    )

    # In Finnish: Asemakaavan diaarinumero
    plan_reference_number = models.CharField(
        verbose_name=_("Plan reference number"), null=True, blank=True, max_length=255
    )

    # In Finnish: Asemakaavan nro.
    plan_number = models.CharField(
        verbose_name=_("Plan number"), max_length=255, null=True, blank=True
    )

    # In Finnish: Päättäjä
    plan_acceptor = models.ForeignKey(
        DecisionMaker,
        verbose_name=_("Plan acceptor"),
        related_name="land_use_agreements",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Asemakaavan lainvoimaisuuspvm
    plan_lawfulness_date = models.DateField(
        verbose_name=_("Plan lawfulness date"), null=True, blank=True
    )

    # In Finnish: Asemakaavan käsittelyvaihe
    state = EnumField(
        InfillDevelopmentCompensationState,
        verbose_name=_("State"),
        null=True,
        blank=True,
        max_length=30,
    )

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Land use agreement")
        verbose_name_plural = pgettext_lazy("Model name", "Land use agreements")

    def __str__(self):
        return "Land use agreement #{}".format(self.id)

    @transaction.atomic
    def create_identifier(self):
        if self.identifier_id:
            return

        if not self.type or not self.municipality or not self.district:
            return

        # lock LandUseAgreementIdentifier table to prevent a (theoretically) possible
        # race condition when increasing the sequence
        with connection.cursor() as cursor:
            cursor.execute("LOCK TABLE %s" % self._meta.db_table)

        max_sequence = LandUseAgreementIdentifier.objects.filter(
            type=self.type, municipality=self.municipality, district=self.district
        ).aggregate(Max("sequence"))["sequence__max"]

        if not max_sequence:
            max_sequence = 0

        identifier = LandUseAgreementIdentifier.objects.create(
            type=self.type,
            municipality=self.municipality,
            district=self.district,
            sequence=max_sequence + 1,
        )

        self.identifier = identifier

    def save(self, *args, **kwargs):
        self.create_identifier()
        super().save(*args, **kwargs)


class LandUseAgreementEstate(NameModel):
    """
    In Finnish: Kohde
    """

    land_use_agreement = models.ForeignKey(
        LandUseAgreement,
        verbose_name=_("Land use agreement"),
        related_name="estate_ids",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    estate_id = models.CharField(
        verbose_name=_("Estate id"), max_length=50, unique=True
    )


class LandUseAgreementDecision(TimeStampedSafeDeleteModel):
    """
    In Finnish: Maankäyttösopimuspäätös
    """

    land_use_agreement = models.ForeignKey(
        LandUseAgreement,
        verbose_name=_("Land use agreement"),
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

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Land use agreement decision")
        verbose_name_plural = pgettext_lazy(
            "Model name", "Land use agreement decisions"
        )


class LandUseAgreementAddress(AbstractAddress):
    land_use_agreement = models.ForeignKey(
        LandUseAgreement,
        verbose_name=_("Land use agreement"),
        related_name="addresses",
        on_delete=models.CASCADE,
    )

    # In Finnish: Ensisijainen osoite
    is_primary = models.BooleanField(verbose_name=_("Is primary?"), default=False)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Land use agreement address")
        verbose_name_plural = pgettext_lazy(
            "Model name", "Land use agreement addresses"
        )


class LandUseAgreementConditionType(NameModel):
    """
    In Finnish: Maankäyttösopimuksen ehdon tyyppi
    """


class LandUseAgreementCondition(TimeStampedSafeDeleteModel):
    """
    In Finnish: Maankäyttösopimuksen ehto
    """

    land_use_agreement = models.ForeignKey(
        LandUseAgreement,
        verbose_name=_("Land use agreement"),
        related_name="conditions",
        on_delete=models.PROTECT,
    )

    # In Finnish: Maankäyttösopimuksen ehdon tyyppi
    type = models.ForeignKey(
        LandUseAgreementConditionType,
        verbose_name=_("Form of management"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Valvontapvm
    due_date = models.DateField(verbose_name=_("Due date"), null=True, blank=True)

    # In Finnish: Valvottu pvm
    sent_date = models.DateField(verbose_name=_("Sent date"), null=True, blank=True)

    # In Finnish: Kommentti
    description = models.TextField(verbose_name=_("Description"), null=True, blank=True)


class LandUseAgreementLitigant(TimeStampedSafeDeleteModel):
    land_use_agreement = models.ForeignKey(
        LandUseAgreement,
        verbose_name=_("Land use agreement"),
        related_name="litigants",
        on_delete=models.CASCADE,
    )

    # In Finnish: Jaettava / Osoittaja
    share_numerator = models.PositiveIntegerField(verbose_name=_("Numerator"))

    # In Finnish: Jakaja / Nimittäjä
    share_denominator = models.PositiveIntegerField(verbose_name=_("Denominator"))

    # In Finnish: Viite
    reference = models.CharField(
        verbose_name=_("Section"), null=True, blank=True, max_length=255
    )

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Land use agreement litigant")
        verbose_name_plural = pgettext_lazy("Model name", "Land use agreement litigant")


class LandUseAgreementLitigantContact(TimeStampedSafeDeleteModel):

    land_use_agreement_litigant = models.ForeignKey(
        LandUseAgreementLitigant,
        verbose_name=_("Land use agreement litigant"),
        related_name="litigant_contacts",
        on_delete=models.PROTECT,
    )

    # In Finnish: Kontaktin tyyppi
    type = EnumField(
        LandUseAgreementLitigantContactType,
        verbose_name=_("Contact type"),
        null=True,
        blank=True,
        max_length=30,
    )

    # In Finnish: Asiakas
    contact = models.ForeignKey(
        Contact,
        verbose_name=_("Contact"),
        related_name="land_use_agreement",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Alkupäivämäärä
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)

    # In Finnish: Loppupäivämäärä
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Land use agreement litigant")
        verbose_name_plural = pgettext_lazy("Model name", "Land use agreement litigant")


class LandUseAgreementInvoice(TimeStampedSafeDeleteModel):
    """
    In Finnish: Lasku
    """

    land_use_agreement = models.ForeignKey(
        LandUseAgreement,
        verbose_name=_("Land use agreement"),
        related_name="invoices",
        on_delete=models.PROTECT,
    )

    # In Finnish: Laskun numero
    number = models.PositiveIntegerField(
        verbose_name=_("Number"), unique=True, null=True, blank=True
    )

    # In Finnish: Laskunsaaja
    recipient = models.ForeignKey(
        Contact, verbose_name=_("Recipient"), related_name="+", on_delete=models.PROTECT
    )

    # In Finnish: Korvauksen määrä €
    compensation_amount = models.DecimalField(
        verbose_name=_("Compensation amount"), decimal_places=2, max_digits=12
    )

    # In Finnish: Korvauksen määrä %
    compensation_amount_percentage = models.DecimalField(
        verbose_name=_("Compensation amount percentage"),
        decimal_places=2,
        max_digits=12,
    )

    # In Finnish: Euroa
    amount = models.DecimalField(
        verbose_name=_("Amount"), decimal_places=2, max_digits=12
    )

    # In Finnish: Allekirjoituspvm
    sign_date = models.DateField(verbose_name=_("Sign date"), null=True, blank=True)

    # In Finnish: Asemakaavan lainvoimaisuuspvm
    plan_lawfulness_date = models.DateField(
        verbose_name=_("Plan lawfulness date"), null=True, blank=True
    )

    # In Finnish: Eräpäivä
    due_date = models.DateField(verbose_name=_(" date"), null=True, blank=True)

    # In Finnish: Lähetyspäivä
    sent_date = models.DateField(verbose_name=_("Sent date"), null=True, blank=True)

    # In Finnish: Maksupäivä
    paid_date = models.DateField(verbose_name=_("Paid date"), null=True, blank=True)

    # In Finnish: Lähetetty SAP:iin
    sent_to_sap_at = models.DateTimeField(
        verbose_name=_("Sent to SAP at"), null=True, blank=True
    )

    def generate_number(self):
        if self.number:
            return self.number

        with transaction.atomic():
            self.number = get_next_value("invoice_numbers", initial_value=1000000)
            self.save()

        return self.number
