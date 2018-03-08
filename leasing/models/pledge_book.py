from django.db import models
from django.utils.translation import ugettext_lazy as _

from .contract import Contract


class PledgeBook(models.Model):
    """
    In Finnish: Panttikirja
    """
    # In Finnish: Sopimus
    contract = models.ForeignKey(Contract, verbose_name=_("Contract"), on_delete=models.PROTECT)

    # In Finnish: Panttikirjan numero
    pledge_book_number = models.CharField(verbose_name=_("Pledge book number"), max_length=255)

    # In Finnish: Panttikirjan pvm
    pledge_book_date = models.DateField(verbose_name=_("Pledge book date"))

    # In Finnish: Panttikirjan kommentti
    pledge_book_comment = models.TextField(verbose_name=_("Pledge book comment"))
