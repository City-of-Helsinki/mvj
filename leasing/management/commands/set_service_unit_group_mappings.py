from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from leasing.management.commands.set_ad_group_mappings import SERVICE_UNITS
from leasing.models import ServiceUnit
from leasing.models.service_unit import ServiceUnitGroupMapping


class Command(BaseCommand):
    help = (
        "Sets the default user group to Service unit mappings. Creates a group for "
        "the Service unit if a group doesn't exist already."
    )

    def handle(self, *args, **options):
        service_units = {su.id: su for su in ServiceUnit.objects.all()}
        for service_unit_data in SERVICE_UNITS:
            if service_unit_data["id"] not in service_units.keys():
                raise CommandError(
                    "Service unit id {} missing. Please load service_unit.json fixture first.".format(
                        service_unit_data["id"]
                    )
                )

        for service_unit_data in SERVICE_UNITS:
            (service_unit_group, created) = Group.objects.get_or_create(
                name=service_unit_data["group_name"]
            )

            ServiceUnitGroupMapping.objects.get_or_create(
                group=service_unit_group,
                service_unit=service_units[service_unit_data["id"]],
            )
