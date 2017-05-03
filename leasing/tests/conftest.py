import factory
from django.contrib.auth.models import User
from pytest_factoryboy import register

from leasing.models import Application, Contact, Lease


@register
class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User


@register
class ApplicationFactory(factory.DjangoModelFactory):
    class Meta:
        model = Application


@register
class ContactFactory(factory.DjangoModelFactory):
    class Meta:
        model = Contact


@register
class LeaseFactory(factory.DjangoModelFactory):
    class Meta:
        model = Lease
