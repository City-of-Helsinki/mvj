from unittest.mock import MagicMock, patch

import pytest

from leasing.importer.usage_distributions import UsageDistributionImporter
from leasing.models.land_area import UsageDistribution


def _get_mock_importer() -> UsageDistributionImporter:
    """Initializes the UsageDistributionImporter with necessary mocks in place."""
    importer = UsageDistributionImporter()
    importer.cursor = MagicMock(return_value=MagicMock())
    importer.initialize_importer = MagicMock()
    return importer


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

    importer = _get_mock_importer()

    with patch(
        "leasing.importer.usage_distributions.rows_to_dict_list",
        return_value=[
            {
                "KG_KKAAVYKS": 5043111,
                "KAAVAYKSIKKOTUNNUS": "1234",
                "C_KAYTJAKAUMA": "1",
                "SELITE": "Pääkäyttötarkoitus",
                "C_RAKOIKEUS": "795",
                "I_RAKOIKEUS": "1000",
            },
            {
                "KG_KKAAVYKS": 5031395,
                "KAAVAYKSIKKOTUNNUS": "1234",
                "C_KAYTJAKAUMA": "1",
                "SELITE": "Pääkäyttötarkoitus",
                "C_RAKOIKEUS": "8100",
                "I_RAKOIKEUS": "1000",
            },
            {
                "KG_KKAAVYKS": 5031395,
                "KAAVAYKSIKKOTUNNUS": "1234",
                "C_KAYTJAKAUMA": "3BB",
                "SELITE": "Liike- tai toimistotilat",
                "C_RAKOIKEUS": "650",
                "I_RAKOIKEUS": "1000",
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
                "KAAVAYKSIKKOTUNNUS": "1234",
                "C_KAYTJAKAUMA": "1",
                "SELITE": "Pääkäyttötarkoitus",
                "C_RAKOIKEUS": "795",
                "I_RAKOIKEUS": "1000",
            },
        ],
    ):
        UsageDistributionImporter.import_usage_distributions(importer)

    assert UsageDistribution.objects.all().count() == 2
    assert master_plan_unit.usage_distributions.count() == 1
    assert second_master_plan_unit.usage_distributions.count() == 1


@pytest.mark.django_db
def test_build_permission_amount(plan_unit_factory, lease_area_factory, lease_factory):
    """
    Build permission amount is correctly imported, depending on available values
    in different columns in Facta database.
    """
    # Create a plan unit whose identifier is used to match usage distributions
    lease_area = lease_area_factory(
        lease=lease_factory(),
        identifier="4321",
        area=2000,
        section_area=2000,
    )
    plan_unit_factory(
        area=100,
        lease_area=lease_area,
        identifier="5678",
        is_master=True,
    )
    importer = _get_mock_importer()

    with patch(
        "leasing.importer.usage_distributions.rows_to_dict_list",
        return_value=[
            {
                "KG_KKAAVYKS": 1111111,
                "KAAVAYKSIKKOTUNNUS": "5678",
                "C_KAYTJAKAUMA": "case1",  # I use these as "identifiers" for each usage distribution. Not a real value.
                "SELITE": "Case 1",
                "C_RAKOIKEUS": "100",  # This should be picked
                "I_RAKOIKEUS": "1001",
            },
            {
                "KG_KKAAVYKS": 2222222,
                "KAAVAYKSIKKOTUNNUS": "5678",
                "C_KAYTJAKAUMA": "case2",
                "SELITE": "Case 2",
                "C_RAKOIKEUS": "200",  # This should be picked
                "I_RAKOIKEUS": None,
            },
            {
                "KG_KKAAVYKS": 3333333,
                "KAAVAYKSIKKOTUNNUS": "5678",
                "C_KAYTJAKAUMA": "case3",
                "SELITE": "Case 3",
                "C_RAKOIKEUS": None,
                "I_RAKOIKEUS": "3001",  # This should be picked
            },
            {
                "KG_KKAAVYKS": 4444444,
                "KAAVAYKSIKKOTUNNUS": "5678",
                "C_KAYTJAKAUMA": "case4",
                "SELITE": "Case 4",
                "C_RAKOIKEUS": None,
                "I_RAKOIKEUS": None,  # Build permission should be "-" as no valid values exist
            },
            {
                "KG_KKAAVYKS": 5555555,
                "KAAVAYKSIKKOTUNNUS": "5678",
                "C_KAYTJAKAUMA": "case5",
                "SELITE": "Case 5",
                "C_RAKOIKEUS": "0",  # This should be picked
                "I_RAKOIKEUS": "5005",
            },
        ],
    ):
        UsageDistributionImporter.import_usage_distributions(importer)

    assert UsageDistribution.objects.get(distribution="case1").build_permission == "100"
    assert UsageDistribution.objects.get(distribution="case2").build_permission == "200"
    assert (
        UsageDistribution.objects.get(distribution="case3").build_permission == "3001"
    )
    assert UsageDistribution.objects.get(distribution="case4").build_permission == "-"
    assert UsageDistribution.objects.get(distribution="case5").build_permission == "0"
