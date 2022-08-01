from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from .filters import UserFilter
from .models import User
from .serializers import UserSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_class = UserFilter
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("username", "first_name", "last_name")
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        qs = super().get_queryset()

        if not self.request.user.has_perm("users.view_user"):
            qs = qs.filter(pk=self.request.user.pk)

        return qs.distinct()
