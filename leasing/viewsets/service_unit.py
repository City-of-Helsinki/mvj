from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.viewsets import ReadOnlyModelViewSet

from leasing.models import ServiceUnit
from leasing.serializers.service_unit import ServiceUnitSerializer


class ServiceUnitViewSet(ReadOnlyModelViewSet):
    queryset = ServiceUnit.objects.all()
    serializer_class = ServiceUnitSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    search_fields = (
        "id",
        "name",
        "description",
        "use_rent_override_receivable_type",
    )
    ordering = ("name",)
