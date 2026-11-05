import logging
import sys
import time
from collections import defaultdict
from typing import Any

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from helusers.models import ADGroup, ADGroupMapping

from leasing.enums import ServiceUnitId
from utils.enums import AuthGroupId, AuthGroupName

logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(stdout_handler)
logger.setLevel(logging.INFO)

DOMAIN_PREFIX = "helsinki1\\"
COMMON_AD_GROUP_PREFIX = "sg_kymp_ad-tunnistamo_mvj_"
SERVICE_UNIT_GROUPS = [
    {
        "group_id": AuthGroupId.PALVELUKOKONAISUUS_MAKE,
        "service_unit_id": ServiceUnitId.MAKE,
        "group_name": AuthGroupName.PALVELUKOKONAISUUS_MAKE,
        "ad_group_part": "",
    },
    {
        "group_id": AuthGroupId.PALVELUKOKONAISUUS_KAMA,
        "service_unit_id": ServiceUnitId.KAMA,
        "group_name": AuthGroupName.PALVELUKOKONAISUUS_KAMA,
        "ad_group_part": "ayp",
    },
    {
        "group_id": AuthGroupId.PALVELUKOKONAISUUS_KUVA_LIPA,
        "service_unit_id": ServiceUnitId.KUVA_LIPA,
        "group_name": AuthGroupName.PALVELUKOKONAISUUS_KUVA_LIPA,
        "ad_group_part": "lipa",
    },
    {
        "group_id": AuthGroupId.PALVELUKOKONAISUUS_KUVA_UPA,
        "service_unit_id": ServiceUnitId.KUVA_UPA,
        "group_name": AuthGroupName.PALVELUKOKONAISUUS_KUVA_UPA,
        "ad_group_part": "upa",
    },
    {
        "group_id": AuthGroupId.PALVELUKOKONAISUUS_KUVA_NUP,
        "service_unit_id": ServiceUnitId.KUVA_NUP,
        "group_name": AuthGroupName.PALVELUKOKONAISUUS_KUVA_NUP,
        "ad_group_part": "nup",
    },
]

ROLE_TO_USER_GROUP_ID_MAP = {
    "selailija": AuthGroupId.SELAILIJA,
    "valmistelijat": AuthGroupId.VALMISTELIJA,
    "sopimusvalmistelija": AuthGroupId.SOPIMUSVALMISTELIJA,
    "syottaja": AuthGroupId.SYOTTAJA,
    "perintalakimies": AuthGroupId.PERINTALAKIMIES,
    "laskuttaja": AuthGroupId.LASKUTTAJA,
    "paakayttaja": AuthGroupId.PAAKAYTTAJA,
}


class Command(BaseCommand):
    help = "Sets predefined AD group mappings for the predefined MVJ groups"

    def handle(self, *args: Any, **options: Any) -> None:
        start = time.monotonic()
        self.clear_existing_mappings()
        self.set_leasing_mappings()
        self.set_landuse_mappings()
        logger.info(
            f"Total AD groups: {ADGroup.objects.count()}, "
            f"total AD group mappings: {ADGroupMapping.objects.count()}, "
            f"elapsed: {time.monotonic() - start:.2f}s"
        )

    def clear_existing_mappings(self) -> None:
        deleted_count, _ = ADGroupMapping.objects.all().delete()
        logger.info(f"Deleted {deleted_count} existing AD group mappings")

    def set_leasing_mappings(self) -> None:
        ad_group_map: defaultdict[str, list[int]] = defaultdict(list)
        for service_unit_group_data in SERVICE_UNIT_GROUPS:
            # Ensure group name with some other id does not exist, remove if exists
            # Cascade deletes possible existing AdGroupMappings
            stale_groups = Group.objects.filter(
                name=service_unit_group_data["group_name"]
            ).exclude(id=service_unit_group_data["group_id"])
            stale_ids = list(stale_groups.values_list("id", flat=True))
            if stale_ids:
                deleted_count, _ = stale_groups.delete()
                logger.info(
                    f"Deleted stale groups {stale_ids} named "
                    f"'{service_unit_group_data['group_name']}' "
                    f"({deleted_count} rows including cascades)"
                )

            service_unit_group, created = Group.objects.update_or_create(
                id=service_unit_group_data["group_id"],
                defaults={"name": service_unit_group_data["group_name"]},
            )
            action = "Created" if created else "Updated"
            logger.info(
                f"{action} service unit group {service_unit_group.id} "
                f"'{service_unit_group.name}'"
            )

            for role_name, user_group_id in ROLE_TO_USER_GROUP_ID_MAP.items():
                ad_group_name = (
                    COMMON_AD_GROUP_PREFIX
                    + (
                        service_unit_group_data["ad_group_part"] + "_"
                        if service_unit_group_data["ad_group_part"]
                        else ""
                    )
                    + role_name
                )

                # Add groups with and without the domain prefix because ADFS returns
                # groups with the domain part, and Entra ID (ex Azure AD) returns
                # groups without the domain part.
                # Role group
                ad_group_map[DOMAIN_PREFIX + ad_group_name].append(user_group_id)
                ad_group_map[ad_group_name].append(user_group_id)

                # Service unit group
                ad_group_map[DOMAIN_PREFIX + ad_group_name].append(
                    service_unit_group.id
                )
                ad_group_map[ad_group_name].append(service_unit_group.id)

        ad_groups = {ad_group.name: ad_group for ad_group in ADGroup.objects.all()}

        for ad_group_name, group_ids in ad_group_map.items():
            if not group_ids:
                logger.info(f"Skipping AD group {ad_group_name}, no group IDs")
                continue
            if ad_group_name not in ad_groups:
                logger.info(f"Creating missing AD group {ad_group_name}")
                ad_groups[ad_group_name] = ADGroup.objects.create(
                    name=ad_group_name, display_name=ad_group_name
                )

            for group_id in group_ids:
                ADGroupMapping.objects.get_or_create(
                    ad_group_id=ad_groups[ad_group_name].id, group_id=group_id
                )

    def set_landuse_mappings(self) -> None:
        """
        Sets permissions for users of Landuse application.
        These users require separate permissions from Leasing,
        but they are currently derived from the same AD groups.
        """
        LANDUSE_MAPPINGS = {
            AuthGroupId.MAANKAYTTOSOPIMUSTEN_SELAILIJA: [
                # -- MAKE
                "sg_kymp_ad-tunnistamo_mvj_selailija",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_selailija",
                # Syöttäjä role for landuse has not been defined, grant only read permissions
                "sg_kymp_ad-tunnistamo_mvj_syottaja",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_syottaja",
                # Perintälakimies role for landuse has not been defined, grant only read permissions
                "sg_kymp_ad-tunnistamo_mvj_perintalakimies",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_perintalakimies",
                # -- KAMA
                "sg_kymp_ad-tunnistamo_mvj_ayp_selailija",
                "sg_kymp_ad-tunnistamo_mvj_ayp_valmistelijat",
                "sg_kymp_ad-tunnistamo_mvj_ayp_sopimusvalmistelija",
                "sg_kymp_ad-tunnistamo_mvj_ayp_syottaja",
                "sg_kymp_ad-tunnistamo_mvj_ayp_perintalakimies",
                "sg_kymp_ad-tunnistamo_mvj_ayp_laskuttaja",
                "sg_kymp_ad-tunnistamo_mvj_ayp_paakayttaja",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_ayp_selailija",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_ayp_valmistelijat",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_ayp_sopimusvalmistelija",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_ayp_syottaja",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_ayp_perintalakimies",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_ayp_laskuttaja",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_ayp_paakayttaja",
                # -- KUVA LIPA
                "sg_kymp_ad-tunnistamo_mvj_lipa_selailija",
                "sg_kymp_ad-tunnistamo_mvj_lipa_valmistelijat",
                "sg_kymp_ad-tunnistamo_mvj_lipa_sopimusvalmistelija",
                "sg_kymp_ad-tunnistamo_mvj_lipa_syottaja",
                "sg_kymp_ad-tunnistamo_mvj_lipa_perintalakimies",
                "sg_kymp_ad-tunnistamo_mvj_lipa_laskuttaja",
                "sg_kymp_ad-tunnistamo_mvj_lipa_paakayttaja",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_lipa_selailija",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_lipa_valmistelijat",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_lipa_sopimusvalmistelija",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_lipa_syottaja",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_lipa_perintalakimies",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_lipa_laskuttaja",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_lipa_paakayttaja",
                # -- KUVA UPA
                "sg_kymp_ad-tunnistamo_mvj_upa_selailija",
                "sg_kymp_ad-tunnistamo_mvj_upa_valmistelijat",
                "sg_kymp_ad-tunnistamo_mvj_upa_sopimusvalmistelija",
                "sg_kymp_ad-tunnistamo_mvj_upa_syottaja",
                "sg_kymp_ad-tunnistamo_mvj_upa_perintalakimies",
                "sg_kymp_ad-tunnistamo_mvj_upa_laskuttaja",
                "sg_kymp_ad-tunnistamo_mvj_upa_paakayttaja",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_upa_selailija",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_upa_valmistelijat",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_upa_sopimusvalmistelija",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_upa_syottaja",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_upa_perintalakimies",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_upa_laskuttaja",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_upa_paakayttaja",
                # -- KUVA NUP
                "sg_kymp_ad-tunnistamo_mvj_nup_selailija",
                "sg_kymp_ad-tunnistamo_mvj_nup_valmistelijat",
                "sg_kymp_ad-tunnistamo_mvj_nup_sopimusvalmistelija",
                "sg_kymp_ad-tunnistamo_mvj_nup_syottaja",
                "sg_kymp_ad-tunnistamo_mvj_nup_perintalakimies",
                "sg_kymp_ad-tunnistamo_mvj_nup_laskuttaja",
                "sg_kymp_ad-tunnistamo_mvj_nup_paakayttaja",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_nup_selailija",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_nup_valmistelijat",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_nup_sopimusvalmistelija",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_nup_syottaja",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_nup_perintalakimies",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_nup_laskuttaja",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_nup_paakayttaja",
            ],
            AuthGroupId.MAANKAYTTOSOPIMUSTEN_VALMISTELIJA: [
                "sg_kymp_ad-tunnistamo_mvj_valmistelijat",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_valmistelijat",
            ],
            AuthGroupId.MAANKAYTTOSOPIMUSTEN_SOPIMUSVALMISTELIJA: [
                "sg_kymp_ad-tunnistamo_mvj_sopimusvalmistelija",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_sopimusvalmistelija",
            ],
            # Syöttäjä role for landuse has not been defined, do not map to any specific AdGroup
            AuthGroupId.MAANKAYTTOSOPIMUSTEN_SYOTTAJA: [],
            AuthGroupId.MAANKAYTTOSOPIMUSTEN_LASKUTTAJA: [
                "sg_kymp_ad-tunnistamo_mvj_laskuttaja",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_laskuttaja",
            ],
            # Perintälakimies role for landuse has not been defined, do not map to any specific AdGroup
            AuthGroupId.MAANKAYTTOSOPIMUSTEN_PERINTALAKIMIES: [],
            AuthGroupId.MAANKAYTTOSOPIMUSTEN_PAAKAYTTAJA: [
                "sg_kymp_ad-tunnistamo_mvj_paakayttaja",
                "helsinki1\\sg_kymp_ad-tunnistamo_mvj_paakayttaja",
            ],
        }

        for group_id, ad_group_names in LANDUSE_MAPPINGS.items():
            if not ad_group_names:
                logger.info(f"No landuse AD groups mapped to group {group_id}")
            for ad_group_name in ad_group_names:
                ad_group, created = ADGroup.objects.get_or_create(
                    name=ad_group_name, defaults={"display_name": ad_group_name}
                )
                if created:
                    logger.info(f"Created missing AD group {ad_group_name}")

                ADGroupMapping.objects.get_or_create(
                    ad_group_id=ad_group.id, group_id=group_id
                )
