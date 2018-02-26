from django.db import models
from django.utils.translation import ugettext_lazy as _

from .contract import Contract


class PledgeBook(models.Model):
    """
    Attributes:
        contract (ForeignKey):
            Name in Finnish: Sopimus
        pledge_book_number (CharField):
            Name in Finnish: Panttikirjan numero
        pledge_book_date (DateField):
            Name in Finnish: Panttikirjan pvm
        pledge_book_comment (TextField):
            Name in Finnish: Panttikirjan kommentti
    """
    contract = models.ForeignKey(
        Contract,
        verbose_name=_("Contract"),
        on_delete=models.PROTECT,
    )

    pledge_book_number = models.CharField(
        verbose_name=_("Pledge book number"),
        max_length=255,
    )

    pledge_book_date = models.DateField(
        verbose_name=_("Pledge book date"),
    )

    pledge_book_comment = models.TextField(
        verbose_name=_("Pledge book comment"),
    )
