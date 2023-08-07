import pytest
from helusers.models import ADGroup, ADGroupMapping


@pytest.mark.django_db
def test_ad_group_mappings_allow_multiple_groups_per_adgroup(group_factory, user):
    laskuttaja_group = group_factory(name="Laskuttaja")
    make_group = group_factory(name="Maanomaisuuden kehittäminen ja tontit")
    atv_group = group_factory(name="ATV")
    joku_group = group_factory(name="Joku")

    ad_make_laskuttaja = ADGroup.objects.create(
        name="ad_make_laskuttaja", display_name="Make laskuttaja"
    )
    ad_atv_laskuttaja = ADGroup.objects.create(
        name="ad_atv_laskuttaja", display_name="ATV laskuttaja"
    )
    ad_joku = ADGroup.objects.create(name="ad_joku", display_name="Joku")

    ADGroupMapping.objects.create(ad_group=ad_make_laskuttaja, group=make_group)
    ADGroupMapping.objects.create(ad_group=ad_atv_laskuttaja, group=atv_group)
    ADGroupMapping.objects.create(ad_group=ad_make_laskuttaja, group=laskuttaja_group)
    ADGroupMapping.objects.create(ad_group=ad_atv_laskuttaja, group=laskuttaja_group)
    ADGroupMapping.objects.create(ad_group=ad_joku, group=joku_group)

    user.update_ad_groups(["ad_make_laskuttaja"])

    assert set(user.groups.all()) == {make_group, laskuttaja_group}
