from auditlog.registry import auditlog
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from enumfields import EnumField
from sequences import get_next_value

from field_permissions.registry import field_permissions
from leasing.enums import DocumentType
from leasing.validators import validate_business_id
from users.models import User

from .mixins import NameModel, TimeStampedSafeDeleteModel


class ContractType(NameModel):
    """
    In Finnish: Sopimuksen tyyppi
    """

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Contract type")
        verbose_name_plural = pgettext_lazy("Model name", "Contract types")


class Contract(TimeStampedSafeDeleteModel):
    """
    In Finnish: Sopimus
    """

    lease = models.ForeignKey(
        "leasing.Lease",
        verbose_name=_("Lease"),
        related_name="contracts",
        null=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Sopimuksen tyyppi
    type = models.ForeignKey(
        ContractType,
        verbose_name=_("Contract type"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Sopimusnumero
    contract_number = models.CharField(
        verbose_name=_("Contract number"), null=True, blank=True, max_length=255
    )

    # In Finnish: Allekirjoituspäivämäärä
    signing_date = models.DateField(
        verbose_name=_("Signing date"), null=True, blank=True
    )

    # In Finnish: Allekirjoitettava mennessä
    sign_by_date = models.DateField(
        verbose_name=_("Sign by date"), null=True, blank=True
    )

    # In Finnish: Kommentti allekirjoitukselle
    signing_note = models.TextField(
        verbose_name=_("Signing note"), null=True, blank=True
    )

    # In Finnish: 1. kutsu lähetetty
    first_call_sent = models.DateField(
        verbose_name=_("First call sent"), null=True, blank=True
    )

    # In Finnish: 2. kutsu lähetetty
    second_call_sent = models.DateField(
        verbose_name=_("Second call sent"), null=True, blank=True
    )

    # In Finnish: 3. kutsu lähetetty
    third_call_sent = models.DateField(
        verbose_name=_("Third call sent"), null=True, blank=True
    )

    # In Finnish: Järjestelypäätös
    is_readjustment_decision = models.BooleanField(
        verbose_name=_("Is readjustment decision"), null=True, blank=True
    )

    # In Finnish: Päätös
    decision = models.ForeignKey(
        "leasing.Decision",
        verbose_name=_("Decision"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: KTJ vuokraoikeustodistuksen linkki
    ktj_link = models.CharField(
        verbose_name=_("KTJ link"), null=True, blank=True, max_length=1024
    )

    # In Finnish: Laitostunnus
    institution_identifier = models.CharField(
        verbose_name=_("Institution identifier"), null=True, blank=True, max_length=255
    )

    executor = models.ForeignKey(
        "users.User",
        verbose_name=_("Executor"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    recursive_get_related_skip_relations = ["lease"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Contract")
        verbose_name_plural = pgettext_lazy("Model name", "Contracts")

    def get_contract_number_sequence_name(self):
        if not self.lease:
            return None

        return self.lease.service_unit.contract_number_sequence_name

    def get_contract_number_sequence_initial_value(self):
        if not self.lease or not self.lease.service_unit.first_contract_number:
            return 1

        return self.lease.service_unit.first_contract_number

    def save(self, *args, **kwargs):
        if (
            self.pk
            or self.contract_number
            or not self.lease
            or not self.get_contract_number_sequence_name()
        ):
            super().save(*args, **kwargs)
            return

        with transaction.atomic():
            self.contract_number = get_next_value(
                self.get_contract_number_sequence_name(),
                initial_value=self.get_contract_number_sequence_initial_value(),
            )
            super().save(*args, **kwargs)


class CollateralType(NameModel):
    """
    In Finnish: Vakuuden laji
    """

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Collateral type")
        verbose_name_plural = pgettext_lazy("Model name", "Collateral types")


class Collateral(models.Model):
    """
    In Finnish: Vakuus
    """

    contract = models.ForeignKey(
        Contract,
        verbose_name=_("Contract"),
        related_name="collaterals",
        on_delete=models.PROTECT,
    )

    # In Finnish: Vakuuden tyyppi
    type = models.ForeignKey(
        CollateralType,
        verbose_name=_("Collateral type"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Vakuuden laji
    other_type = models.CharField(
        verbose_name=_("Other type"), null=True, blank=True, max_length=255
    )

    # In Finnish: Numero
    number = models.CharField(
        verbose_name=_("Number"), null=True, blank=True, max_length=255
    )

    # In Finnish: Alkupvm
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)

    # In Finnish: Loppupvm
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    # In Finnish: Panttikirjan pvm
    deed_date = models.DateField(verbose_name=_("Deed date"), null=True, blank=True)

    # In Finnish: Määrä
    total_amount = models.DecimalField(
        verbose_name=_("Total amount"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: Maksettu pvm
    paid_date = models.DateField(verbose_name=_("Paid date"), null=True, blank=True)

    # In Finnish: Palautettu pvm
    returned_date = models.DateField(
        verbose_name=_("Returned date"), null=True, blank=True
    )

    # In Finnish: Palautuksen merkitsijä
    returned_by = models.ForeignKey(
        User,
        verbose_name=_("Returned by"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Huomautus
    note = models.TextField(verbose_name=_("Note"), null=True, blank=True)

    # In Finnish: Vierasvelkapanttaus
    third_party_pledge = models.BooleanField(
        verbose_name=_("Third party pledge"), default=False
    )

    # In Finnish: Vierasvelkapanttauksen antajan nimi
    third_party_pledgor_name = models.CharField(
        verbose_name=_("Third party pledgor name"),
        null=True,
        blank=True,
        max_length=255,
    )

    # In Finnish: Vierasvelkapanttauksen antajan Y-tunnus
    third_party_pledgor_business_id = models.CharField(
        verbose_name=_("Third party pledgor Business ID"),
        null=True,
        blank=True,
        max_length=255,
        validators=[validate_business_id],
    )

    # In Finnish: Vakuuden antajan nimi
    pledgor_name = models.CharField(
        verbose_name=_("Pledgor name"), null=True, blank=True, max_length=255
    )

    # In Finnish: Vakuuden antajan Henkilötunnus
    pledgor_national_identification_number = models.CharField(
        verbose_name=_("Pledgor National identification number"),
        null=True,
        blank=True,
        max_length=255,
    )

    # In Finnish: Vakuuden antajan Y-tunnus
    pledgor_business_id = models.CharField(
        verbose_name=_("Pledgor Business ID"),
        null=True,
        blank=True,
        max_length=255,
        validators=[validate_business_id],
    )

    # In Finnish: Jälkipanttaus
    subordinate_pledge = models.BooleanField(
        verbose_name=_("Subordinate pledge"),
        default=False,
    )

    # In Finnish: Jälkipantin saajan nimi
    subordinate_pledgee_name = models.CharField(
        verbose_name=_("Subordinate pledgee name"),
        null=True,
        blank=True,
        max_length=255,
    )

    # In Finnish: Jälkipantin saajan y-tunnus
    subordinate_pledgee_business_id = models.CharField(
        verbose_name=_("Subordinate pledgee business ID"),
        null=True,
        blank=True,
        max_length=255,
        validators=[validate_business_id],
    )

    # In Finnish: Sopimusosapuoli
    # TODO should be named "tenant" or just "party"?
    contract_party = models.ManyToManyField(
        "leasing.Tenant",
        related_name="+",
        blank=True,
    )

    # In Finnish: Sopimusosapuolen henkilötunnus
    contract_party_national_identification_number = models.CharField(
        verbose_name=_("National identification number"),
        null=True,
        blank=True,
        max_length=255,
    )

    # In Finnish: Sopimusosapuolen Y-tunnus
    contract_party_business_id = models.CharField(
        verbose_name=_("Business ID"),
        null=True,
        blank=True,
        max_length=255,
        validators=[validate_business_id],
    )

    # In Finnish: Tilinumero
    account_number = models.CharField(
        verbose_name=_("Account number"),
        null=True,
        blank=True,
        max_length=255,
    )

    # In Finnish: Vakuusasiakirjan laji
    document_type = EnumField(
        DocumentType,
        verbose_name=_("Document type"),
        max_length=30,
        null=True,
        blank=True,
    )

    # In Finnish: Takausnumero
    # TODO: should be collateral_number, or something else?
    # TODO: add this to Omavelkainen takaus
    guarantee_number = models.CharField(
        verbose_name=_("Guarantee number"),
        null=True,
        blank=True,
        max_length=255,
    )

    recursive_get_related_skip_relations = ["contract"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Collateral")
        verbose_name_plural = pgettext_lazy("Model name", "Collaterals")


class ContractChange(models.Model):
    """
    In Finnish: Sopimuksen muutos
    """

    contract = models.ForeignKey(
        Contract,
        verbose_name=_("Contract"),
        related_name="contract_changes",
        on_delete=models.PROTECT,
    )

    # In Finnish: Allekirjoituspäivä
    signing_date = models.DateField(
        verbose_name=_("Signing date"), null=True, blank=True
    )

    # In Finnish: Allekirjoitettava mennessä
    sign_by_date = models.DateField(
        verbose_name=_("Sign by date"), null=True, blank=True
    )

    # In Finnish: 1. kutsu lähetetty
    first_call_sent = models.DateField(
        verbose_name=_("First call sent"), null=True, blank=True
    )

    # In Finnish: 2. kutsu lähetetty
    second_call_sent = models.DateField(
        verbose_name=_("Second call sent"), null=True, blank=True
    )

    # In Finnish: 3. kutsu lähetetty
    third_call_sent = models.DateField(
        verbose_name=_("Third call sent"), null=True, blank=True
    )

    # In Finnish: Selite
    description = models.TextField(verbose_name=_("Description"), null=True, blank=True)

    # In Finnish: Päätös
    decision = models.ForeignKey(
        "leasing.Decision",
        verbose_name=_("Decision"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    executor = models.ForeignKey(
        "users.User",
        verbose_name=_("Executor"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    recursive_get_related_skip_relations = ["contract", "decision"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Contract change")
        verbose_name_plural = pgettext_lazy("Model name", "Contract changes")


auditlog.register(Contract)
auditlog.register(ContractChange)
auditlog.register(Collateral)

field_permissions.register(Contract, exclude_fields=["lease"])
field_permissions.register(ContractChange, exclude_fields=["contract"])
field_permissions.register(Collateral, exclude_fields=["contract"])
