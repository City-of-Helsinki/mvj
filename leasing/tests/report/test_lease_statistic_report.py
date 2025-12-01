import datetime

import pytest

from leasing.report.lease.lease_statistic_report import (
    _get_latest_decision,
    get_latest_decision_date,
    get_latest_decision_maker,
    get_latest_decision_type_name,
)


@pytest.mark.django_db
def test_get_latest_decision_returns_none_when_no_decisions(lease_factory):
    lease = lease_factory()
    result = _get_latest_decision(lease)
    assert result is None


@pytest.mark.django_db
def test_get_latest_decision_returns_single_decision(lease_factory, decision_factory):
    """Simplest positive case"""
    lease = lease_factory()
    decision = decision_factory(
        lease=lease,
        decision_date=datetime.date(2025, 1, 1),
    )
    result = _get_latest_decision(lease)
    assert result == decision


@pytest.mark.django_db
def test_get_latest_decision_returns_decision_with_latest_date(
    lease_factory, decision_factory
):
    lease = lease_factory()
    older_decision = decision_factory(  # noqa: F841 (unused variable by purpose)
        lease=lease,
        decision_date=datetime.date(2020, 1, 1),
    )
    latest_decision = decision_factory(
        lease=lease,
        decision_date=datetime.date(2025, 1, 1),
    )
    middle_decision = decision_factory(  # noqa: F841 (unused variable by purpose)
        lease=lease,
        decision_date=datetime.date(2023, 1, 1),
    )
    result = _get_latest_decision(lease)
    assert result == latest_decision


@pytest.mark.django_db
def test_get_latest_decision_handles_none_decision_dates(
    lease_factory, decision_factory
):
    lease = lease_factory()
    decision_without_date = decision_factory(  # noqa: F841 (unused variable by purpose)
        lease=lease,
        decision_date=None,
    )
    decision_with_date = decision_factory(
        lease=lease,
        decision_date=datetime.date(2025, 1, 1),
    )
    result = _get_latest_decision(lease)
    # Decision with date should be preferred over None
    assert result == decision_with_date


@pytest.mark.django_db
def test_get_latest_decision_maker_returns_empty_string_when_no_decisions(
    lease_factory,
):
    lease = lease_factory()
    result = get_latest_decision_maker(lease)
    assert result == ""


@pytest.mark.django_db
def test_get_latest_decision_maker_returns_empty_string_when_decision_maker_is_none(
    lease_factory, decision_factory
):
    lease = lease_factory()
    decision_factory(
        lease=lease,
        decision_date=datetime.date(2025, 1, 1),
        decision_maker=None,
    )
    result = get_latest_decision_maker(lease)
    assert result == ""


@pytest.mark.django_db
def test_get_latest_decision_maker_returns_empty_string_when_decision_maker_name_is_empty(
    lease_factory, decision_factory, decision_maker_factory
):
    lease = lease_factory()
    decision_maker = decision_maker_factory(name="")
    decision_factory(
        lease=lease,
        decision_date=datetime.date(2025, 1, 1),
        decision_maker=decision_maker,
    )
    result = get_latest_decision_maker(lease)
    assert result == ""


@pytest.mark.django_db
def test_get_latest_decision_maker_returns_decision_maker_name(
    lease_factory, decision_factory, decision_maker_factory
):
    """Simplest positive case"""
    lease = lease_factory()
    decision_maker = decision_maker_factory(name="City Council")
    decision_factory(
        lease=lease,
        decision_date=datetime.date(2025, 1, 1),
        decision_maker=decision_maker,
    )
    result = get_latest_decision_maker(lease)
    assert result == "City Council"


@pytest.mark.django_db
def test_get_latest_decision_maker_returns_latest_decision_maker_name(
    lease_factory, decision_factory, decision_maker_factory
):
    lease = lease_factory()
    older_decision_maker = decision_maker_factory(name="Old Council")
    latest_decision_maker = decision_maker_factory(name="New Council")
    decision_factory(
        lease=lease,
        decision_date=datetime.date(2020, 1, 1),
        decision_maker=older_decision_maker,
    )
    decision_factory(
        lease=lease,
        decision_date=datetime.date(2025, 1, 1),
        decision_maker=latest_decision_maker,
    )
    result = get_latest_decision_maker(lease)
    assert result == "New Council"


@pytest.mark.django_db
def test_get_latest_decision_date_returns_empty_string_when_no_decisions(
    lease_factory,
):
    lease = lease_factory()
    result = get_latest_decision_date(lease)
    assert result == ""


@pytest.mark.django_db
def test_get_latest_decision_date_returns_empty_string_when_decision_date_is_none(
    lease_factory, decision_factory
):
    lease = lease_factory()
    decision_factory(
        lease=lease,
        decision_date=None,
    )
    result = get_latest_decision_date(lease)
    assert result == ""


@pytest.mark.django_db
def test_get_latest_decision_date_returns_decision_date(
    lease_factory, decision_factory
):
    """Simplest positive case"""
    lease = lease_factory()
    expected_date = datetime.date(2025, 1, 1)
    decision_factory(
        lease=lease,
        decision_date=expected_date,
    )
    result = get_latest_decision_date(lease)
    assert result == expected_date


@pytest.mark.django_db
def test_get_latest_decision_date_returns_latest_decision_date(
    lease_factory, decision_factory
):
    lease = lease_factory()
    older_date = datetime.date(2020, 1, 1)
    latest_date = datetime.date(2025, 1, 1)

    decision_factory(
        lease=lease,
        decision_date=older_date,
    )
    decision_factory(
        lease=lease,
        decision_date=latest_date,
    )
    result = get_latest_decision_date(lease)
    assert result == latest_date


@pytest.mark.django_db
def test_get_latest_decision_type_name_returns_empty_string_when_no_decisions(
    lease_factory,
):
    lease = lease_factory()
    result = get_latest_decision_type_name(lease)
    assert result == ""


@pytest.mark.django_db
def test_get_latest_decision_type_name_returns_empty_string_when_type_is_none(
    lease_factory, decision_factory
):
    lease = lease_factory()
    decision_factory(
        lease=lease,
        decision_date=datetime.date(2025, 1, 1),
        type=None,
    )
    result = get_latest_decision_type_name(lease)
    assert result == ""


@pytest.mark.django_db
def test_get_latest_decision_type_name_returns_type_name(
    lease_factory, decision_factory, decision_type_factory
):
    """Simplest positive case"""
    lease = lease_factory()
    decision_type = decision_type_factory(name="Approval Decision")
    decision_factory(
        lease=lease,
        decision_date=datetime.date(2025, 1, 1),
        type=decision_type,
    )
    result = get_latest_decision_type_name(lease)
    assert result == "Approval Decision"


@pytest.mark.django_db
def test_get_latest_decision_type_name_returns_latest_type_name(
    lease_factory, decision_factory, decision_type_factory
):
    lease = lease_factory()
    older_type = decision_type_factory(name="Old Decision Type")
    latest_type = decision_type_factory(name="New Decision Type")

    decision_factory(
        lease=lease,
        decision_date=datetime.date(2020, 1, 1),
        type=older_type,
    )
    decision_factory(
        lease=lease,
        decision_date=datetime.date(2025, 1, 1),
        type=latest_type,
    )
    result = get_latest_decision_type_name(lease)
    assert result == "New Decision Type"


@pytest.mark.django_db
def test_get_latest_decision_type_name_returns_empty_when_type_name_is_empty(
    lease_factory, decision_factory, decision_type_factory
):
    lease = lease_factory()
    decision_type = decision_type_factory(name="")
    decision_factory(
        lease=lease,
        decision_date=datetime.date(2025, 1, 1),
        type=decision_type,
    )
    result = get_latest_decision_type_name(lease)
    assert result == ""
