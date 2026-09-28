import factory
from django.contrib.auth.models import Group, Permission

from users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    @factory.post_generation
    def service_units(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        for service_unit in extracted:
            self.service_units.add(service_unit)

    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        self.user_permissions.set(Permission.objects.filter(codename__in=extracted))


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Group
