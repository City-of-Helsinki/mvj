from collections import defaultdict

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from helusers.models import ADGroup, ADGroupMapping

DOMAIN_PREFIX = "helsinki1\\"
COMMON_AD_GROUP_PREFIX = "sg_kymp_ad-tunnistamo_mvj_"
SERVICE_UNITS = [
    {
        "id": 1,
        "group_name": "Maaomaisuuden kehittäminen ja tontit",
        "ad_group_part": "",
    },
    {"id": 2, "group_name": "Alueiden käyttö ja valvonta", "ad_group_part": "ayp"},
    {"id": 3, "group_name": "KuVa / Liikuntapaikkapalvelut", "ad_group_part": "lipa"},
    {"id": 4, "group_name": "KuVa / Ulkoilupalvelut", "ad_group_part": "upa"},
    {"id": 5, "group_name": "KuVa / Nuorisopalvelut", "ad_group_part": "nup"},
]

# 1 Selailija
# 2 Valmistelija
# 3 Sopimusvalmistelija
# 4 Syöttäjä
# 5 Perintälakimies
# 6 Laskuttaja
# 7 Pääkäyttäjä
ROLE_TO_GROUP_ID_MAP = {
    "selailija": 1,
    "valmistelijat": 2,
    "sopimusvalmistelija": 3,
    "syottaja": 4,
    "perintalakimies": 5,
    "laskuttaja": 6,
    "paakayttaja": 7,
}


class Command(BaseCommand):
    help = "Sets predefined AD group mappings for the predefined MVJ groups"

    def handle(self, *args, **options):
        ad_group_map = defaultdict(list)
        for service_unit_data in SERVICE_UNITS:
            (service_unit_group, created) = Group.objects.get_or_create(
                name=service_unit_data["group_name"]
            )

            for role_name, group_id in ROLE_TO_GROUP_ID_MAP.items():
                ad_group_name = (
                    COMMON_AD_GROUP_PREFIX
                    + (
                        service_unit_data["ad_group_part"] + "_"
                        if service_unit_data["ad_group_part"]
                        else ""
                    )
                    + role_name
                )

                # Add groups with and without the domain prefix because ADFS returns
                # groups with the domain part, and Entra ID (ex Azure AD) returns
                # groups without the domain part.
                # Role group
                ad_group_map[DOMAIN_PREFIX + ad_group_name].append(group_id)
                ad_group_map[ad_group_name].append(group_id)

                # Service unit group
                ad_group_map[DOMAIN_PREFIX + ad_group_name].append(
                    service_unit_group.id
                )
                ad_group_map[ad_group_name].append(service_unit_group.id)

        ad_groups = {ad_group.name: ad_group for ad_group in ADGroup.objects.all()}

        for ad_group_name, group_ids in ad_group_map.items():
            if not group_ids:
                continue
            if ad_group_name not in ad_groups:
                self.stdout.write("Creating missing AD group {}".format(ad_group_name))
                ad_groups[ad_group_name] = ADGroup.objects.create(
                    name=ad_group_name, display_name=ad_group_name
                )

            for group_id in group_ids:
                ADGroupMapping.objects.get_or_create(
                    ad_group_id=ad_groups[ad_group_name].id, group_id=group_id
                )
