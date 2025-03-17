from rest_framework import viewsets

from leasing.filters import OldDwellingsInHousingCompaniesPriceIndexFilter
from leasing.models.periodic_rent_adjustment import (
    OldDwellingsInHousingCompaniesPriceIndex,
)
from leasing.serializers.periodic_rent_adjustment import (
    OldDwellingsInHousingCompaniesPriceIndexSerializer,
)


class PeriodicRentAdjustmentPriceIndexViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OldDwellingsInHousingCompaniesPriceIndex.objects.all()
    serializer_class = OldDwellingsInHousingCompaniesPriceIndexSerializer
    filterset_class = OldDwellingsInHousingCompaniesPriceIndexFilter
