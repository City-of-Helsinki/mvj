from django.db import models
from django.utils.translation import ugettext_lazy as _


class ContractChange(models.Model):
    """Contract change

    Name in Finnish: Sopimuksen muutokset

    modification_signing_date (DateField):
        Name in Finnish: Allekirjoituspäivä
    to_be_signed_by (DateField):
        Name in Finnish: Allekirjoitettava mennessä
    first_call_sent (DateField):
        Name in Finnish: 1. kutsu lähetetty
    second_call_sent (DateField):
        Name in Finnish: 2. kutsu lähetetty
    third_call_sent (DateField):
        Name in Finnish: 3. kutsu lähetetty
    modification_description (TextField):
        Name in Finnish: Selite
    linked_rule (CharField):
        Name in Finnish: Päätös
    """
    modification_signing_date = models.DateField(
        verbose_name=_("Modification signing date"),
    )

    to_be_signed_by = models.DateField(
        verbose_name=_("To be signed by"),
    )

    first_call_sent = models.DateField(
        verbose_name=_("First call sent"),
    )

    second_call_sent = models.DateField(
        verbose_name=_("Second call sent"),
    )

    third_call_sent = models.DateField(
        verbose_name=_("Third call sent"),
    )

    modification_description = models.TextField(
        verbose_name=_("Modification description")
    )
