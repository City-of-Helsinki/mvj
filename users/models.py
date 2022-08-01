from django.contrib import admin
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from helusers.models import AbstractUser
from rest_framework.authtoken.models import Token


class User(AbstractUser):
    service_units = models.ManyToManyField("leasing.ServiceUnit", related_name="users")

    recursive_get_related_skip_relations = [
        "auth_token",
        "logentry",
        "emaillog",
        "emaillogs",
        "Emaillog_recipients+",
        "groups",
        "user_permissions",
        "ad_groups",
        "favourite",
        "answer",
        "plotsearch",
        "areasearch",
        "areasearchstatusnote",
        "targetstatus",
        "informationcheck",
        "service_units",
    ]

    @admin.display(boolean=True, description=_("Token exists"))
    def has_token(self) -> bool:
        return Token.objects.filter(user=self).exists()

    @transaction.atomic
    def update_service_units(self):
        """Updates users Service Units according to Service Unit Group Mappings"""
        from leasing.models.service_unit import ServiceUnitGroupMapping

        group_mappings = {
            mapping.group: mapping.service_unit
            for mapping in ServiceUnitGroupMapping.objects.all()
        }
        managed_service_units = set(group_mappings.values())
        old_service_units = set(
            self.service_units.filter(id__in=[s.id for s in managed_service_units])
        )
        new_service_units = set(
            [group_mappings[x] for x in self.groups.all() if x in group_mappings]
        )

        service_units_to_delete = old_service_units.difference(new_service_units)
        if service_units_to_delete:
            self.service_units.remove(*service_units_to_delete)

        service_units_to_add = new_service_units.difference(old_service_units)
        if service_units_to_add:
            self.service_units.add(*service_units_to_add)
