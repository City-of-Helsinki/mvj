from rest_framework.viewsets import ReadOnlyModelViewSet

from leasing.models import Vat
from leasing.serializers.vat import VatSerializer


class VatViewSet(ReadOnlyModelViewSet):
    queryset = Vat.objects.all()
    serializer_class = VatSerializer
