from unittest.mock import MagicMock, patch

import pytest

from leasing.importer.usage_distributions import UsageDistributionImporter
from leasing.models.land_area import UsageDistribution


@pytest.mark.django_db
def test_usage_distribution_count(
    lease_test_data, lease_area_factory, lease_factory, plan_unit_factory
):
    """
    Correct number of usage distributions are saved during import.
    """
    master_plan_unit = plan_unit_factory(
        area=100,
        lease_area=lease_test_data["lease_area"],
        identifier="1234",
        is_master=True,
    )
    second_lease_area = lease_area_factory(
        lease=lease_factory(),
        identifier="9876",
        area=2000,
        section_area=2000,
    )
    second_master_plan_unit = plan_unit_factory(
        area=200,
        lease_area=second_lease_area,
        identifier="1234",
        is_master=True,
    )

    importer = UsageDistributionImporter()
    importer.cursor = MagicMock(return_value=MagicMock())
    importer.initialize_importer = MagicMock()

    with patch(
        "leasing.importer.usage_distributions.rows_to_dict_list",
        return_value=[
            {
                "KG_KKAAVYKS": 5043111,
                "C_KAAVAYKSIKKOTUNNUS": "1234",
                "C_KAYTJAKAUMA": "1",
                "MV_KOODISTO0_C_SELITE": "Pääkäyttötarkoitus",
                "C_PAASIVUK": "P",
                "C_RAKOIKEUS": "795",
            },
            {
                "KG_KKAAVYKS": 5031395,
                "C_KAAVAYKSIKKOTUNNUS": "1234",
                "C_KAYTJAKAUMA": "1",
                "MV_KOODISTO0_C_SELITE": "Pääkäyttötarkoitus",
                "C_PAASIVUK": "P",
                "C_RAKOIKEUS": "8100",
            },
            {
                "KG_KKAAVYKS": 5031395,
                "C_KAAVAYKSIKKOTUNNUS": "1234",
                "C_KAYTJAKAUMA": "3BB",
                "MV_KOODISTO0_C_SELITE": "Liike- tai toimistotilat",
                "C_PAASIVUK": "S",
                "C_RAKOIKEUS": "650",
            },
        ],
    ):
        UsageDistributionImporter.import_usage_distributions(importer)

    assert UsageDistribution.objects.all().count() == 6
    assert master_plan_unit.usage_distributions.count() == 3
    assert second_master_plan_unit.usage_distributions.count() == 3

    with patch(
        "leasing.importer.usage_distributions.rows_to_dict_list",
        return_value=[
            {
                "KG_KKAAVYKS": 5043111,
                "C_KAAVAYKSIKKOTUNNUS": "1234",
                "C_KAYTJAKAUMA": "1",
                "MV_KOODISTO0_C_SELITE": "Pääkäyttötarkoitus",
                "C_PAASIVUK": "P",
                "C_RAKOIKEUS": "795",
            },
        ],
    ):
        UsageDistributionImporter.import_usage_distributions(importer)

    assert UsageDistribution.objects.all().count() == 2
    assert master_plan_unit.usage_distributions.count() == 1
    assert second_master_plan_unit.usage_distributions.count() == 1
