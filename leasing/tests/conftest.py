import factory
from django.contrib.auth.models import User
from pytest_factoryboy import register

from leasing.models import Lease


@register
class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User


@register
class LeaseFactory(factory.DjangoModelFactory):
    class Meta:
        model = Lease
