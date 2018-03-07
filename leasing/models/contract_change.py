from django.db import models
from django.utils.translation import ugettext_lazy as _


class ContractChange(models.Model):
    """Name in Finnish: Sopimuksen muutokset"""
    # Name in Finnish: Allekirjoituspäivä
    modification_signing_date = models.DateField(verbose_name=_("Modification signing date"))

    # Name in Finnish: Allekirjoitettava mennessä
    to_be_signed_by = models.DateField(verbose_name=_("To be signed by"))

    # Name in Finnish: 1. kutsu lähetetty
    first_call_sent = models.DateField(verbose_name=_("First call sent"))

    # Name in Finnish: 2. kutsu lähetetty
    second_call_sent = models.DateField(verbose_name=_("Second call sent"))

    # Name in Finnish: 3. kutsu lähetetty
    third_call_sent = models.DateField(verbose_name=_("Third call sent"))

    # Name in Finnish: Selite
    modification_description = models.TextField(verbose_name=_("Modification description"))

    # Name in Finnish: Päätös
    linked_rule = models.CharField(verbose_name=_("Administration number"), max_length=255)
