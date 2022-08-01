from django_filters.rest_framework import FilterSet

from leasing.filters import NumberInFilter
from users.models import User


class UserFilter(FilterSet):
    service_unit = NumberInFilter(field_name="service_units__id")

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
        ]
