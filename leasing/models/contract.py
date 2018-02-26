from django.db import models
from django.utils.translation import ugettext_lazy as _

from .mixins import ConfigurableTextChoice


class ContractType(ConfigurableTextChoice):
    pass


class ContractSetupDecision(ConfigurableTextChoice):
    pass


class ContractLinkedRule(ConfigurableTextChoice):
    pass


class Contract(models.Model):
    """Contract

    Name in Finnish: Sopimus

    Attributes:
        contract_type (ForeignKey):
            Name in Finnish: Sopimuksen tyyppi
        contract_number (CharField):
            Name in Finnish: Sopimusnumero
        signing_date (DateField):
            Name in Finnish: Allekirjoituspäivämäärä
        signing_date_comment (TextField):
            Name in Finnish: Kommentti allekirjoitukselle
        setup_decision (ForeignKey):
            Name in Finnish: Järjestelypäätös
        linked_rule (ForeignKey):
            Name in Finnish: Päätös
        ktj_document (CharField):
            Name in Finnish: KTJ vuokraoikeustodistuksen linkki
        lease_deposit_number (CharField):
            Name in Finnish: Vuokravakuusnumero
        lease_deposit_starting_date (DateField):
            Name in Finnish: Vuokravakuus alkupvm
        lease_deposit_ending_date (DateField):
            Name in Finnish: Vuokravakuus loppupvm
        lease_deposit_comment (TextField):
            Name in Finnish: Vuokravakuus kommentti
        administration_number (CharField):
            Name in Finnish: Laitostunnus
    """
    contract_type = models.ForeignKey(
        ContractType,
        verbose_name=_("Contract type"),
        on_delete=models.PROTECT,
    )

    contract_number = models.CharField(
        verbose_name=_("Contract number"),
        max_length=255,
    )

    signing_date = models.DateField(
        verbose_name=_("Signing date"),
    )

    signing_date_comment = models.TextField(
        verbose_name=_("Signing date comment"),
    )

    setup_decision = models.ForeignKey(
        ContractSetupDecision,
        verbose_name=_("Setup decision"),
        on_delete=models.PROTECT,
    )

    linked_rule = models.ForeignKey(
        ContractLinkedRule,
        verbose_name=_("Linked rule"),
        on_delete=models.PROTECT,
    )

    ktj_document = models.CharField(
        verbose_name=_("Ktj document"),
        max_length=255,
    )

    lease_deposit_number = models.CharField(
        verbose_name=_("Lease deposit number"),
        max_length=255,
    )

    lease_deposit_starting_date = models.DateField(
        verbose_name=_("Lease deposit starting date"),
    )

    lease_deposit_ending_date = models.DateField(
        verbose_name=_("Lease deposit ending date"),
    )

    lease_deposit_comment = models.TextField(
        verbose_name=_("Lease deposit comment"),
    )

    administration_number = models.CharField(
        verbose_name=_("Administration number"),
        max_length=255,
    )
