from collections import defaultdict
from itertools import chain

import django.contrib.auth.models
from django.contrib import admin
from django.core.cache import cache
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from helsinki_gdpr.models import SerializableMixin
from helusers.models import AbstractUser, ADGroupMapping
from rest_framework.authtoken.models import Token


class OfficerUserManager(models.Manager):
    def get_queryset(self):
        """
        Returns users that are officers of City of Helsinki (employees).
        This is determined by checking if the user has any AD groups,
        and that the AD group has at least one ADGroupMapping.
        Technically officer == AD user with a mapped group (as of now).
        """
        return (
            super()
            .get_queryset()
            .filter(
                is_active=True,
                ad_groups__isnull=False,
                # Ensure that the ADGroup the user has does have ADGroupMapping,
                # meaning a group that the system expects to be an officer.
                ad_groups__id__in=ADGroupMapping.objects.values_list(
                    "ad_group_id", flat=True
                ),
            )
            .distinct()
        )


class User(AbstractUser, SerializableMixin):
    # Default manager needs to be set due to having custom manager.
    objects = django.contrib.auth.models.UserManager()

    # Manager for users that are officers of Helsinki
    officers = OfficerUserManager()

    service_units = models.ManyToManyField("leasing.ServiceUnit", related_name="users")

    # GDPR API, meant for PlotSearch app users
    serialize_fields = (
        {"name": "uuid"},
        {"name": "first_name"},
        {"name": "last_name"},
        {"name": "email"},
        {"name": "date_joined"},
        # forms.Attachment
        {"name": "attachment"},
        # plotsearch.AreaSearch
        {"name": "areasearch_set"},
    )

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

    def sync_groups_from_ad(self):
        """Determine which Django groups to add or remove based on AD groups

        Supports setting multiple Django groups by one AD group"""
        cache_key = f"sync_groups_from_ad_{self.id}"
        if cache.get(cache_key):
            return

        cache.set(cache_key, True, timeout=600)  # 10 minutes

        ad_group_mappings = ADGroupMapping.objects.select_related("ad_group", "group")
        mappings = defaultdict(list)
        for ad_group_mapping in ad_group_mappings:
            mappings[ad_group_mapping.ad_group].append(ad_group_mapping.group)

        user_ad_groups = set(self.ad_groups.filter(groups__isnull=False))
        managed_groups = set(chain(*mappings.values()))
        old_groups = set(
            self.groups.filter(id__in=[group.id for group in managed_groups])
        )
        new_groups = set(chain(*[mappings[x] for x in user_ad_groups if x in mappings]))

        groups_to_delete = old_groups.difference(new_groups)
        if groups_to_delete:
            self.groups.remove(*groups_to_delete)

        groups_to_add = new_groups.difference(old_groups)
        if groups_to_add:
            self.groups.add(*groups_to_add)

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
