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

    # DEBUG TO SEE WHAT IS GOING ON
    def perform_authentication(self, request):
        try:
            super().perform_authentication(request)
        except Exception as e:
            print(
                "Authentication failed on {} {}: {} | User-Agent: {}".format(
                    request.method,
                    request.get_full_path(),
                    str(e),
                    request.META.get("HTTP_USER_AGENT", ""),
                )
            )

    def get_queryset(self):
        try:
            qs = super().get_queryset()

            if not self.request.user.has_perm("users.view_user"):
                qs = qs.filter(pk=self.request.user.pk)

            return qs.distinct()
        except Exception as e:
            print(
                "Failed to get queryset on {} {}: {} | User-Agent: {}".format(
                    self.request.method,
                    self.request.get_full_path(),
                    str(e),
                    self.request.META.get("HTTP_USER_AGENT", ""),
                )
            )


class OfficerViewSet(UserViewSet):
    queryset = User.officers.all()
