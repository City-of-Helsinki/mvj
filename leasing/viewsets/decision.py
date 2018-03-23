from rest_framework import viewsets

from leasing.filters import DecisionFilter
from leasing.models import Decision
from leasing.serializers.contract import DecisionSerializer
from leasing.viewsets.utils import AuditLogMixin


class DecisionViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = Decision.objects.all()
    serializer_class = DecisionSerializer
    filter_class = DecisionFilter
