import factory
from django.contrib.auth.models import User
from pytest_factoryboy import register

from leasing.models import Application, Contact, Lease, Note, Rent


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


@register
class NoteFactory(factory.DjangoModelFactory):
    class Meta:
        model = Note


@register
class RentFactory(factory.DjangoModelFactory):
    class Meta:
        model = Rent
