from django.contrib.auth.models import User
from django_filters import rest_framework as filters
from rest_framework import viewsets

from users.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filter_fields = ['is_staff', 'username']
