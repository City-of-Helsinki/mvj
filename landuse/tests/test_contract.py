import datetime

import pytest

from landuse.models.agreement import LandUseAgreement
from landuse.models.contract import (
    Contract,
    MortgageDeedCollateral,
    MortgageDeedPropertyIdentifier,
)


@pytest.fixture
def contract(db):
    agreement = LandUseAgreement.objects.create(identifier="test-agreement")
    return Contract.objects.create(agreement=agreement)


@pytest.fixture
def mortgage_deed_collateral(contract):
    return MortgageDeedCollateral(
        contract=contract,
        guarantee_type=MortgageDeedCollateral.CollateralType.MORTGAGE_DEED,
        mortgage_deed_number="123",
        mortgage_deed_date=datetime.date(2026, 1, 1),
    )


def test_mortgage_deed_collateral_rejects_facility_identifier_for_property_target(
    mortgage_deed_collateral,
):
    mortgage_deed_collateral.target = MortgageDeedCollateral.CollateralTarget.PROPERTY
    mortgage_deed_collateral.facility_identifier = "facility-123"

    with pytest.raises(
        ValueError, match="Facility identifier cannot be set for property target."
    ):
        mortgage_deed_collateral.save()


def test_mortgage_deed_collateral_requires_facility_identifier_for_facility_target(
    mortgage_deed_collateral,
):
    mortgage_deed_collateral.target = MortgageDeedCollateral.CollateralTarget.FACILITY

    with pytest.raises(
        ValueError, match="Facility identifier must be set for facility target."
    ):
        mortgage_deed_collateral.save()


def test_property_identifier_rejects_facility_target(mortgage_deed_collateral):
    mortgage_deed_collateral.target = MortgageDeedCollateral.CollateralTarget.FACILITY
    mortgage_deed_collateral.facility_identifier = "facility-123"
    mortgage_deed_collateral.save()
    property_identifier = MortgageDeedPropertyIdentifier(
        collateral=mortgage_deed_collateral,
        identifier="123-456-789-0",
    )

    with pytest.raises(
        ValueError, match="Property identifier cannot be set for facility target."
    ):
        property_identifier.save()
