from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from enumfields import EnumField

from leasing.enums import PeriodicRentAdjustmentType

from .mixins import TimeStampedModel, TimeStampedSafeDeleteModel


class OldDwellingsInHousingCompaniesPriceIndex(TimeStampedModel):
    """
    In Finnish: Vanhojen osakeasuntojen hintaindeksi

    This price index has been decided to be used in the periodic rent
    adjustment. It can be thought of as the concrete implementation of a
    hypothetical "PeriodicRentAdjustmentPriceIndex", even though there are no
    other indexes currently used for this purpose in MVJ.

    From my understanding of the StatFi API, a unique price index is identified
    by the source database table URL and code of the index. A single source
    table can hold multiple indexes, and a single code can be used in multiple
    tables.

    Members:
        code: Code for the index's table column. Example: "ketj_P_QA_T". \
              Same code is shared between tables for different intervals, e.g. \
              yearly or quarterly.
        name: Name of the index. Example: "Index (2020=100)".
        comment: Comment for the index's table column.
        source: Source of the data.
        source_table_updated: UTC timestamp when the source table was last updated.
        source_table_label: Label for the source table.
        url: API endpoint URL.
    """

    # Maximum lengths are arbitrary, but set to avoid extra large input.
    CHARFIELD_MAX_LENGTH = 255

    code = models.CharField(
        verbose_name=_("Index code"),
        max_length=CHARFIELD_MAX_LENGTH,
        unique=True,
    )
    name = models.CharField(
        verbose_name=_("Index name"),
        max_length=CHARFIELD_MAX_LENGTH,
    )
    comment = models.TextField(verbose_name=_("Region"), blank=True)
    source = models.CharField(
        verbose_name=_("Data source"),
        blank=True,
        max_length=CHARFIELD_MAX_LENGTH,
    )
    source_table_updated = models.DateTimeField(
        verbose_name=_("Source table updated"), null=True
    )
    source_table_label = models.TextField(
        verbose_name=_("Source table label"),
        blank=True,
    )
    url = models.CharField(
        verbose_name=_("API endpoint URL"),
        max_length=CHARFIELD_MAX_LENGTH,
    )

    class Meta:
        verbose_name = pgettext_lazy(
            "model name", "price index of old dwellings in housing companies"
        )
        verbose_name_plural = pgettext_lazy(
            "model name", "price indexes of old dwellings in housing companies"
        )


class IndexPointFigureYearly(TimeStampedModel):
    """
    In Finnish: Indeksipisteluku, vuosittain

    Holds the index point figures.
    Currently only used with the newer price indexes related to Periodic Rent
    Adjustment (Tasotarkistus).

    The yearly point figure is expected to be the average of all point figures
    from the same year from this same index that use a smaller recording
    inverval.
    For example, the yearly point figure is the average of the year's quarterly
    point figures.

    Members:
        index: Reference to the index this point figure is for.
        value: Numeric value of the point figure. Example: 101.5.
        year: Year for the point figure. Example: 2020.
        region: Geographical region for index value. Example: "pks" for \
                Pääkaupunkiseutu / Greater Helsinki area
        comment: Comment for the point figure. Example: "* preliminary data\r\n"
    """

    index = models.ForeignKey(
        OldDwellingsInHousingCompaniesPriceIndex,
        verbose_name=_("Index"),
        on_delete=models.PROTECT,
        related_name="point_figures",
    )
    # max_digits is arbitrary for the point figure. No need to limit it, although 7
    # should be enough if the point figures are at most in the 100s of thousands.
    # Largest point figure in the system at the moment is year 1914's index
    # with a value around 260 000.
    value = models.DecimalField(
        verbose_name=_("Value"),
        decimal_places=1,
        max_digits=8,
        null=True,
    )
    year = models.PositiveSmallIntegerField(verbose_name=_("Year"))

    # Max lengths here are arbitrary, but set to avoid extra large input.
    region = models.CharField(verbose_name=_("Region"), blank=True, max_length=255)
    comment = models.TextField(verbose_name=_("Comment"), blank=True)

    class Meta:
        verbose_name = pgettext_lazy("model name", "index point figure")
        verbose_name_plural = pgettext_lazy("model name", "index point figures")
        constraints = [
            models.UniqueConstraint(
                fields=["index", "year"], name="unique_price_index_point_figure_yearly"
            )
        ]
        ordering = ("-index", "-year")


class PeriodicRentAdjustment(TimeStampedSafeDeleteModel):
    """
    In Finnish: Tasotarkistus

    If a rent includes a periodic rent adjustment, the rent's amount will be
    adjusted based on the values referenced by the instance of this model.

    The high level idea is to tie the rent to a price index, and adjust the rent
    amount every 20 or 10 years based on the index's point figure values at the
    time of the adjustment.
    """

    # In Finnish: Tasotarkistuksen hintaindeksi
    price_index = models.ForeignKey(
        OldDwellingsInHousingCompaniesPriceIndex,
        verbose_name=_("Price index for periodic rent adjustment"),
        related_name="+",
        on_delete=models.PROTECT,
        blank=False,
        null=False,
    )
    # In Finnish: Tasotarkistuksen tyyppi
    adjustment_type = EnumField(
        enum=PeriodicRentAdjustmentType,
        verbose_name=_("Periodic rent adjustment type"),
        max_length=20,
        null=False,
        blank=False,
    )
    # In Finnish: Tasotarkistusindeksin pisteluku vuokran alkaessa (edellisen vuoden keskiarvo)
    starting_point_figure_value = models.DecimalField(
        verbose_name=_("Price index point figure value at the start of the rent"),
        decimal_places=1,
        max_digits=8,
        null=False,
        blank=False,
    )
    starting_point_figure_year = models.PositiveSmallIntegerField(
        verbose_name=_("Year of the starting point figure"),
        null=False,
        blank=False,
    )
