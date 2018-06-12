from rest_framework import viewsets

from leasing.filters import IndexFilter
from leasing.models.rent import Index
from leasing.serializers.rent import IndexSerializer


class IndexViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Index.objects.all()
    serializer_class = IndexSerializer
    filter_class = IndexFilter
