from django.db import models
from django.utils.translation import ugettext_lazy as _

from leasing.enums import LEASE_IDENTIFIER_DISTRICT, LEASE_IDENTIFIER_MUNICIPALITY, LEASE_IDENTIFIER_TYPE
from leasing.models.mixins import TimestampedModelMixin


class Lease(TimestampedModelMixin):
    type = models.CharField(
        verbose_name=_("Type"),
        max_length=2,
        choices=LEASE_IDENTIFIER_TYPE,
    )

    municipality = models.CharField(
        verbose_name=_("Municipality"),
        max_length=1,
        choices=LEASE_IDENTIFIER_MUNICIPALITY,
    )

    district = models.CharField(
        verbose_name=_("District"),
        max_length=2,
        choices=LEASE_IDENTIFIER_DISTRICT,
    )

    sequence = models.PositiveIntegerField(
        verbose_name=_("Sequence number"),
    )

    start_date = models.DateField(
        verbose_name=_("Start date"),
        null=True,
        blank=True,
    )

    end_date = models.DateField(
        verbose_name=_("End date"),
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.get_identifier()

    def get_identifier(self):
        '''
        The lease identifier is constructed out of type, municipality,
        district, and sequence, in that order. For example, a residence (A1) in
        Helsinki (1), Vallila (22) would be A1122-1.
        '''
        return '{}{}{}-{}'.format(self.type, self.municipality, self.district, self.sequence)

    class Meta:
        unique_together = ('type', 'municipality', 'district', 'sequence')
