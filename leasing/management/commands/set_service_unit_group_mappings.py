import logging
import sys

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from leasing.models import ServiceUnit
from leasing.models.service_unit import ServiceUnitGroupMapping
from utils.management.commands.set_ad_group_mappings import SERVICE_UNIT_GROUPS

logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(stdout_handler)
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = (
        "Sets the default user group to Service unit mappings. Creates a group for "
        "the Service unit if a group doesn't exist already."
    )

    def clear_service_unit_mappings(self):
        deleted_count, _ = ServiceUnitGroupMapping.objects.all().delete()
        logger.info(f"Deleted {deleted_count} existing service unit group mappings")

    @transaction.atomic
    def handle(self, *args, **options):
        self.clear_service_unit_mappings()
        service_units = {su.id: su for su in ServiceUnit.objects.all()}
        for service_unit_group_data in SERVICE_UNIT_GROUPS:
            if service_unit_group_data["service_unit_id"] not in service_units.keys():
                raise CommandError(
                    "Service unit id {} missing. Please load service_unit.json fixture first.".format(
                        service_unit_group_data["service_unit_id"]
                    )
                )

        for service_unit_group_data in SERVICE_UNIT_GROUPS:
            # Ensure group name with some other id does not exist, remove if exists
            # Cascade deletes possible existing AdGroupMappings
            Group.objects.filter(name=service_unit_group_data["group_name"]).exclude(
                id=service_unit_group_data["group_id"]
            ).delete()
            service_unit_group, _ = Group.objects.update_or_create(
                id=service_unit_group_data["group_id"],
                defaults={"name": service_unit_group_data["group_name"]},
            )

            ServiceUnitGroupMapping.objects.get_or_create(
                group=service_unit_group,
                service_unit=service_units[service_unit_group_data["service_unit_id"]],
            )
            logger.info(
                f"Mapped group '{service_unit_group.name}' to service unit {service_unit_group_data["service_unit_id"]}"
            )
