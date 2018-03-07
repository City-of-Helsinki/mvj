from django.db import models
from django.utils.translation import ugettext_lazy as _

from .mixins import NameModel


class ContractType(NameModel):
    pass


class ContractSetupDecision(NameModel):
    pass


class ContractLinkedRule(NameModel):
    pass


class Contract(models.Model):
    """Name in Finnish: Sopimus"""
    # Name in Finnish: Sopimuksen tyyppi
    contract_type = models.ForeignKey(ContractType, verbose_name=_("Contract type"), on_delete=models.PROTECT)

    # Name in Finnish: Sopimusnumero
    contract_number = models.CharField(verbose_name=_("Contract number"), max_length=255)

    # Name in Finnish: Allekirjoituspäivämäärä
    signing_date = models.DateField(verbose_name=_("Signing date"))

    # Name in Finnish: Kommentti allekirjoitukselle
    signing_date_comment = models.TextField(verbose_name=_("Signing date comment"))

    # Name in Finnish: Järjestelypäätös
    setup_decision = models.ForeignKey(ContractSetupDecision, verbose_name=_("Setup decision"),
                                       on_delete=models.PROTECT)

    # Name in Finnish: Päätös
    linked_rule = models.ForeignKey(ContractLinkedRule, verbose_name=_("Linked rule"), on_delete=models.PROTECT)

    # Name in Finnish: KTJ vuokraoikeustodistuksen linkki
    ktj_document = models.CharField(verbose_name=_("Ktj document"), max_length=255)

    # Name in Finnish: Vuokravakuusnumero
    lease_deposit_number = models.CharField(verbose_name=_("Lease deposit number"), max_length=255)

    # Name in Finnish: Vuokravakuus alkupvm
    lease_deposit_starting_date = models.DateField(verbose_name=_("Lease deposit starting date"))

    # Name in Finnish: Vuokravakuus loppupvm
    lease_deposit_ending_date = models.DateField(verbose_name=_("Lease deposit ending date"))

    # Name in Finnish: Vuokravakuus kommentti
    lease_deposit_comment = models.TextField(verbose_name=_("Lease deposit comment"))

    # Name in Finnish: Laitostunnus
    administration_number = models.CharField(verbose_name=_("Administration number"), max_length=255)
