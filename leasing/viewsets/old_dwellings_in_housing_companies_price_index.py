from rest_framework import viewsets

from leasing.filters import OldDwellingsInHousingCompaniesPriceIndexFilter
from leasing.models import OldDwellingsInHousingCompaniesPriceIndex
from leasing.serializers.rent import OldDwellingsInHousingCompaniesPriceIndexSerializer


class OldDwellingsInHousingCompaniesPriceIndexViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OldDwellingsInHousingCompaniesPriceIndex.objects.all()
    serializer_class = OldDwellingsInHousingCompaniesPriceIndexSerializer
    filterset_class = OldDwellingsInHousingCompaniesPriceIndexFilter