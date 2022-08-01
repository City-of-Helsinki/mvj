from auditlog.registry import auditlog
from django.db import models, transaction
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from sequences import get_next_value

from field_permissions.registry import field_permissions

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

    land_use_agreement = models.ForeignKey(
        "leasing.LandUseAgreement",
        verbose_name=_("Land use agreement"),
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

    # In Finnish: Huomautus
    note = models.TextField(verbose_name=_("Note"), null=True, blank=True)

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
