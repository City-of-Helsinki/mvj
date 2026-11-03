from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from leasing.models.service_unit import ServiceUnitGroupMapping
from utils.enums import AuthGroupName

GROUPS = [
    # User roles
    AuthGroupName.SELAILIJA,
    AuthGroupName.VALMISTELIJA,
    AuthGroupName.SOPIMUSVALMISTELIJA,
    AuthGroupName.SYOTTAJA,
    AuthGroupName.PERINTALAKIMIES,
    AuthGroupName.LASKUTTAJA,
    AuthGroupName.PAAKAYTTAJA,
    AuthGroupName.MAANKAYTTOSOPIMUSTEN_SELAILIJA,
    AuthGroupName.MAANKAYTTOSOPIMUSTEN_VALMISTELIJA,
    AuthGroupName.MAANKAYTTOSOPIMUSTEN_SOPIMUSVALMISTELIJA,
    AuthGroupName.MAANKAYTTOSOPIMUSTEN_SYOTTAJA,
    AuthGroupName.MAANKAYTTOSOPIMUSTEN_PERINTALAKIMIES,
    AuthGroupName.MAANKAYTTOSOPIMUSTEN_LASKUTTAJA,
    AuthGroupName.MAANKAYTTOSOPIMUSTEN_PAAKAYTTAJA,
    # Service units
    AuthGroupName.PALVELUKOKONAISUUS_MAKE,
    AuthGroupName.PALVELUKOKONAISUUS_KAMA,
    AuthGroupName.PALVELUKOKONAISUUS_KUVA_LIPA,
    AuthGroupName.PALVELUKOKONAISUUS_KUVA_UPA,
    AuthGroupName.PALVELUKOKONAISUUS_KUVA_NUP,
]


class Command(BaseCommand):
    """
    Makes copies of GROUPS with the same permissions, and attaches the TEST groups to service units.
    The test groups are named "TEST <group name>".
    Since groups are synced from AD groups and flushed periodically,
    this is a way to make permissions stick for e.g. devs.
    """

    def handle(self, *args, **options):
        groups = Group.objects.filter(name__in=GROUPS)
        for group in groups:
            test_group_name = f"TEST {group.name}"
            test_group = self._copy_test_group(group, test_group_name)
            self._copy_group_permissions(group, test_group)
            self._create_service_unit_group_mappings(group, test_group)

    def _copy_test_group(self, group, test_group_name):
        test_group, _ = Group.objects.get_or_create(
            name=test_group_name,
            defaults={"id": group.id + 1000, "name": test_group_name},
        )
        return test_group

    def _copy_group_permissions(self, group, test_group):
        test_group.permissions.set(group.permissions.all())

    def _create_service_unit_group_mappings(self, group, test_group):
        service_units = [mapping.service_unit for mapping in group.service_units.all()]
        for service_unit in service_units:
            ServiceUnitGroupMapping.objects.get_or_create(
                group=test_group, service_unit=service_unit
            )
