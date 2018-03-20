from django.db import models
from django.utils.translation import ugettext_lazy as _

from .mixins import NameModel, TimeStampedSafeDeleteModel


class ContractType(NameModel):
    pass


class ContractSetupDecision(NameModel):
    pass


class ContractDecision(NameModel):
    pass


class Contract(TimeStampedSafeDeleteModel):
    """
    In Finnish: Sopimus
    """
    lease = models.ForeignKey('leasing.Lease', verbose_name=_("Lease"), related_name='contracts',
                              on_delete=models.PROTECT)

    # In Finnish: Sopimuksen tyyppi
    type = models.ForeignKey(ContractType, verbose_name=_("Contract type"), on_delete=models.PROTECT)

    # In Finnish: Sopimusnumero
    contract_number = models.CharField(verbose_name=_("Contract number"), null=True, blank=True, max_length=255)

    # In Finnish: Allekirjoituspäivämäärä
    signing_date = models.DateField(verbose_name=_("Signing date"), null=True, blank=True)

    # In Finnish: Kommentti allekirjoitukselle
    signing_note = models.TextField(verbose_name=_("Signing note"), null=True, blank=True)

    # In Finnish: Järjestelypäätös
    readjustment_decision = models.ForeignKey(ContractSetupDecision, verbose_name=_("Readjustment decision"), null=True,
                                              blank=True, on_delete=models.PROTECT)

    # In Finnish: Päätös
    decision = models.ForeignKey(ContractDecision, verbose_name=_("Decision"), null=True, blank=True,
                                 on_delete=models.PROTECT)

    # In Finnish: KTJ vuokraoikeustodistuksen linkki
    ktj_link = models.CharField(verbose_name=_("KTJ link"), null=True, blank=True, max_length=1024)

    # In Finnish: Vuokravakuusnumero
    collateral_number = models.CharField(verbose_name=_("Collateral number"), null=True, blank=True, max_length=255)

    # In Finnish: Vuokravakuus alkupvm
    collateral_start_date = models.DateField(verbose_name=_("Collateral starting date"), null=True, blank=True)

    # In Finnish: Vuokravakuus loppupvm
    collateral_end_date = models.DateField(verbose_name=_("Collateral ending date"), null=True, blank=True)

    # In Finnish: Vuokravakuus kommentti
    collateral_note = models.TextField(verbose_name=_("Collateral note"), null=True, blank=True)

    # In Finnish: Laitostunnus
    institution_identifier = models.CharField(verbose_name=_("Institution identifier"), null=True, blank=True,
                                              max_length=255)


class MortgageDocument(models.Model):
    """
    In Finnish: Panttikirja
    """
    contract = models.ForeignKey(Contract, verbose_name=_("Contract"), related_name='mortgage_documents',
                                 on_delete=models.PROTECT)

    # In Finnish: Panttikirjan numero
    number = models.CharField(verbose_name=_("Number"), null=True, blank=True, max_length=255)

    # In Finnish: Panttikirjan päivämäärä
    date = models.DateField(verbose_name=_("Date"), null=True, blank=True)

    # In Finnish: Panttikirjan kommentti
    note = models.TextField(verbose_name=_("Note"), null=True, blank=True)


class ContractChange(models.Model):
    """
    In Finnish: Sopimuksen muutos
    """
    contract = models.ForeignKey(Contract, verbose_name=_("Contract"), related_name='contract_changes',
                                 on_delete=models.PROTECT)

    # In Finnish: Allekirjoituspäivä
    signing_date = models.DateField(verbose_name=_("Signing date"), null=True, blank=True)

    # In Finnish: Allekirjoitettava mennessä
    sign_by_date = models.DateField(verbose_name=_("Sign by date"), null=True, blank=True)

    # In Finnish: 1. kutsu lähetetty
    first_call_sent = models.DateField(verbose_name=_("First call sent"), null=True, blank=True)

    # In Finnish: 2. kutsu lähetetty
    second_call_sent = models.DateField(verbose_name=_("Second call sent"), null=True, blank=True)

    # In Finnish: 3. kutsu lähetetty
    third_call_sent = models.DateField(verbose_name=_("Third call sent"), null=True, blank=True)

    # In Finnish: Selite
    description = models.TextField(verbose_name=_("Description"), null=True, blank=True)

    # In Finnish: Päätös
    decision = models.CharField(verbose_name=_("Decision"), null=True, blank=True, max_length=255)
