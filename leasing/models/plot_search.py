from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from leasing.models.mixins import NameModel, TimeStampedSafeDeleteModel
from users.models import User


class PlotSearchType(NameModel):
    """
    In Finnish: Hakutyyppi
    """

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Plot search type")
        verbose_name_plural = pgettext_lazy("Model name", "Plot search types")


class PlotSearchSubtype(NameModel):
    """
    In Finnish: Haun alatyyppi
    """

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Plot search subtype")
        verbose_name_plural = pgettext_lazy("Model name", "Plot search subtypes")


class PlotSearchStage(NameModel):
    """
    In Finnish: Haun vaihe
    """

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Plot search stage")
        verbose_name_plural = pgettext_lazy("Model name", "Plot search stages")


class PlotSearch(TimeStampedSafeDeleteModel, NameModel):
    """
    In Finnish: Tonttihaku
    """

    # In Finnish: Valmistelija
    preparer = models.ForeignKey(
        User,
        verbose_name=_("Preparer"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Hakutyyppi
    type = models.ForeignKey(
        PlotSearchType,
        verbose_name=_("Type"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Hakutyyppi
    subtype = models.ForeignKey(
        PlotSearchSubtype,
        verbose_name=_("Subtype"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Alkuaika
    begin_at = models.DateTimeField(verbose_name=_("Begin at"), null=True, blank=True)

    # In Finnish: Loppuaika
    end_at = models.DateTimeField(verbose_name=_("End at"), null=True, blank=True)

    # In Finnish: Haun vaihe
    stage = models.ForeignKey(
        PlotSearchStage,
        verbose_name=_("Stage"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Plot search")
        verbose_name_plural = pgettext_lazy("Model name", "Plot searches")

    def __str__(self):
        return "Plot search #{}".format(self.id)
