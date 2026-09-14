import datetime
from decimal import Decimal
from io import BytesIO
from zipfile import ZipFile

import pytest
from django.utils import timezone

from leasing.enums import AreaUnit, BasisOfRentType, BasisOfRentZone
from leasing.management.commands.set_report_permissions import DEFAULT_REPORT_PERMS
from leasing.report.lease.lease_basis_of_rent import LeaseBasisOfRentReport
from leasing.report.viewset import ENABLED_REPORTS


@pytest.mark.django_db
def test_lease_basis_of_rent_report_filters_and_serializes(
    lease_factory,
    lease_basis_of_rent_factory,
    service_unit_factory,
    intended_use_factory,
):
    included_service_unit = service_unit_factory()
    excluded_service_unit = service_unit_factory()
    lease_intended_use = intended_use_factory(service_unit=included_service_unit)
    active_lease = lease_factory(
        service_unit=included_service_unit,
        intended_use=lease_intended_use,
        end_date=datetime.date(2030, 1, 1),
    )
    expired_lease = lease_factory(
        service_unit=included_service_unit,
        end_date=datetime.date(2020, 1, 1),
    )
    other_service_unit_lease = lease_factory(service_unit=excluded_service_unit)
    lease_basis_of_rent_factory(
        lease=active_lease,
        type=BasisOfRentType.LEASE,
        area=Decimal("100.00"),
        zone=BasisOfRentZone.ZONE_1,
        area_unit=AreaUnit.SQUARE_METRE,
        amount_per_area=Decimal("10.00"),
        profit_margin_percentage=Decimal("5.00"),
        discount_percentage=Decimal("10.00"),
        locked_at=timezone.now(),
    )
    lease_basis_of_rent_factory(
        lease=expired_lease,
        area=Decimal("100.00"),
        area_unit=AreaUnit.SQUARE_METRE,
        locked_at=timezone.now(),
    )
    lease_basis_of_rent_factory(
        lease=other_service_unit_lease,
        area=Decimal("100.00"),
        area_unit=AreaUnit.SQUARE_METRE,
        locked_at=timezone.now(),
    )
    lease_basis_of_rent_factory(
        lease=active_lease,
        area=Decimal("100.00"),
        area_unit=AreaUnit.SQUARE_METRE,
    )

    report = LeaseBasisOfRentReport()
    data = report.get_data(
        {
            "service_unit": [included_service_unit],
            "only_active_leases": True,
        }
    )
    serialized_data = report.serialize_data(data)

    assert len(serialized_data) == 1
    assert serialized_data[0]["lease_identifier"]["name"] == (
        active_lease.get_identifier_string()
    )
    assert serialized_data[0]["lease_intended_use"] == lease_intended_use.name
    assert serialized_data[0]["service_unit"] == included_service_unit.name
    assert serialized_data[0]["is_lease_active"] is True
    assert serialized_data[0]["type"] == BasisOfRentType.LEASE.value
    assert serialized_data[0]["zone"] == BasisOfRentZone.ZONE_1.value
    assert serialized_data[0]["area_unit"] == AreaUnit.SQUARE_METRE.value
    assert serialized_data[0]["amount_per_area"] == Decimal("10.00")
    assert serialized_data[0]["initial_year_rent"] == Decimal("50.00")
    assert serialized_data[0]["discounted_rent"] == Decimal("45.00")


@pytest.mark.django_db
def test_lease_basis_of_rent_report_includes_child_basis_as_a_separate_row(
    lease_factory,
    lease_basis_of_rent_factory,
):
    lease = lease_factory()
    parent = lease_basis_of_rent_factory(
        lease=lease,
        type=BasisOfRentType.LEASE,
        area=Decimal("100.00"),
        area_unit=AreaUnit.SQUARE_METRE,
        locked_at=timezone.now(),
    )
    lease_basis_of_rent_factory(
        lease=lease,
        parent=parent,
        type=BasisOfRentType.MAST,
        area=Decimal("10.00"),
        area_unit=AreaUnit.SQUARE_METRE,
        locked_at=timezone.now(),
    )

    report = LeaseBasisOfRentReport()
    serialized_data = report.serialize_data(
        report.get_data({"service_unit": [], "only_active_leases": False})
    )
    child_data = next(
        row for row in serialized_data if row["type"] == BasisOfRentType.MAST.value
    )

    assert len(serialized_data) == 2
    assert child_data["lease_identifier"]["name"] == lease.get_identifier_string()
    assert "parent_id" not in child_data


@pytest.mark.django_db
@pytest.mark.parametrize("excluded_object", ["basis_of_rent", "lease"])
def test_lease_basis_of_rent_report_excludes_archived_or_deleted_data(
    lease_factory,
    lease_basis_of_rent_factory,
    excluded_object,
):
    lease = lease_factory()
    basis_of_rent = lease_basis_of_rent_factory(
        lease=lease,
        area=Decimal("100.00"),
        area_unit=AreaUnit.SQUARE_METRE,
        locked_at=timezone.now(),
    )

    if excluded_object == "basis_of_rent":
        basis_of_rent.archived_at = timezone.now()
        basis_of_rent.save(update_fields=["archived_at"])
    else:
        lease.delete()

    report = LeaseBasisOfRentReport()

    assert (
        list(report.get_data({"service_unit": [], "only_active_leases": False})) == []
    )


@pytest.mark.django_db
def test_lease_basis_of_rent_report_exports_to_excel(
    lease_factory,
    lease_basis_of_rent_factory,
):
    lease = lease_factory()
    parent = lease_basis_of_rent_factory(
        lease=lease,
        area=Decimal("100.00"),
        area_unit=AreaUnit.SQUARE_METRE,
        locked_at=timezone.now(),
    )
    lease_basis_of_rent_factory(
        lease=lease,
        parent=parent,
        area=Decimal("10.00"),
        area_unit=AreaUnit.SQUARE_METRE,
        locked_at=timezone.now(),
    )

    report = LeaseBasisOfRentReport()
    report.set_form({})
    report.form.is_valid()
    spreadsheet = report.data_as_excel(
        report.serialize_data(
            report.get_data({"service_unit": [], "only_active_leases": False})
        )
    )

    with ZipFile(BytesIO(spreadsheet)) as workbook:
        shared_strings = workbook.read("xl/sharedStrings.xml")

    assert lease.get_identifier_string().encode() in shared_strings


def test_lease_basis_of_rent_report_is_enabled():
    assert LeaseBasisOfRentReport in ENABLED_REPORTS
    assert LeaseBasisOfRentReport.slug in DEFAULT_REPORT_PERMS
