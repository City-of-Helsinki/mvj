from django.db import models
from django.utils.translation import ugettext_lazy as _

from leasing.models.lease import Lease
from leasing.models.mixins import TimestampedModelMixin


class Asset(TimestampedModelMixin):
    PLOT = 1
    REAL_ESTATE = 2
    ALLOTMENT_GARDEN_PARCEL = 3

    ASSET_TYPE = (
        (PLOT, _("Plot")),
        (REAL_ESTATE, _("Real estate")),
        (ALLOTMENT_GARDEN_PARCEL, _("Allotment garden parcel")),
    )

    type = models.PositiveSmallIntegerField(
        verbose_name=_("Type"),
        choices=ASSET_TYPE,
        null=True,
    )

    leases = models.ManyToManyField(
        Lease,
        verbose_name=_("Leases"),
        related_name='assets',
        blank=True,
    )

    address = models.CharField(
        verbose_name=_("Address"),
        max_length=255,
    )

    surface_area = models.PositiveIntegerField(
        verbose_name=_("Surface area in square meters"),
        null=True,
        blank=True,
    )

    legacy_id = models.PositiveIntegerField(
        verbose_name=_("ID in the legacy system"),
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta:
        verbose_name = _("Asset")
        verbose_name_plural = _("Assets")

    def __str__(self):
        return self.address
