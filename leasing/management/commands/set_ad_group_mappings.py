from django.core.management.base import BaseCommand
from helusers.models import ADGroup, ADGroupMapping

# 1 Selailija
# 2 Valmistelija
# 3 Sopimusvalmistelija
# 4 Syöttäjä
# 5 Perintälakimies
# 6 Laskuttaja
# 7 Pääkäyttäjä
AD_GROUP_MAP = {
    r"helsinki1\sg_kymp_ad-tunnistamo_mvj_selailija": [1],
    r"helsinki1\sg_kymp_ad-tunnistamo_mvj_valmistelijat": [2],
    r"helsinki1\sg_kymp_ad-tunnistamo_mvj_sopimusvalmistelija": [3],
    r"helsinki1\sg_kymp_ad-tunnistamo_mvj_syottaja": [4],
    r"helsinki1\sg_kymp_ad-tunnistamo_mvj_perintalakimies": [5],
    r"helsinki1\sg_kymp_ad-tunnistamo_mvj_laskuttaja": [6],
    r"helsinki1\sg_kymp_ad-tunnistamo_mvj_paakayttaja": [7],
}


class Command(BaseCommand):
    help = 'Sets predefined AD group mappings for the predefined MVJ groups'

    def handle(self, *args, **options):
        ad_groups = {ad_group.name: ad_group for ad_group in ADGroup.objects.filter(name__in=AD_GROUP_MAP.keys())}

        for ad_group_name, group_ids in AD_GROUP_MAP.items():
            if ad_group_name not in ad_groups or not group_ids:
                continue

            for group_id in group_ids:
                ADGroupMapping.objects.get_or_create(ad_group_id=ad_groups[ad_group_name].id, group_id=group_id)
