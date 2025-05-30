import pytest
from helusers.models import ADGroup

from leasing.models.contract import Contract
from leasing.serializers.contract import (
    ContractChangeCreateUpdateSerializer,
    ContractCreateUpdateSerializer,
)
from users.models import User


@pytest.mark.django_db
def test_contract_change_update_serializer_executor_field(
    lease_factory, contract_factory, user_factory
):
    lease = lease_factory()
    contract: Contract = contract_factory(lease=lease)

    officer_user: User = user_factory(username="officer")
    ad_group = ADGroup.objects.create(name="test_ad_group")
    officer_user.ad_groups.add(ad_group)  # This makes the user an officer
    officer_user.save()

    regular_user = user_factory(username="regular")

    contract_data = {
        "type": {"id": contract.type.id},
        "contract_number": "TEST123",
        "signing_date": "2025-01-01",
    }

    # Test with officer user (should be valid)
    serializer = ContractCreateUpdateSerializer(
        data={**contract_data, "executor": {"id": officer_user.id}}
    )
    assert serializer.is_valid(), f"Validation errors: {serializer.errors}"

    # Test with regular user (should be invalid)
    serializer = ContractCreateUpdateSerializer(
        data={**contract_data, "executor": {"id": regular_user.id}}
    )
    assert not serializer.is_valid()
    assert "executor" in serializer.errors

    # Test with null executor (should be valid as `allow_null=True`)
    serializer = ContractCreateUpdateSerializer(
        data={**contract_data, "executor": None}
    )
    assert serializer.is_valid(), f"Validation errors: {serializer.errors}"


@pytest.mark.django_db
def test_contract_change_change_update_serializer_executor_field(
    lease_factory,
    contract_factory,
    user_factory,
):
    lease = lease_factory()
    contract: Contract = contract_factory(lease=lease)

    officer_user: User = user_factory(username="officer")
    ad_group = ADGroup.objects.create(name="test_ad_group")
    officer_user.ad_groups.add(ad_group)  # This makes the user an officer
    officer_user.save()

    regular_user = user_factory(username="regular")

    contract_change_data = {
        "contract": {"id": contract.id},
    }

    # Test with officer user (should be valid)
    serializer = ContractChangeCreateUpdateSerializer(
        data={**contract_change_data, "executor": {"id": officer_user.id}}
    )
    assert serializer.is_valid(), f"Validation errors: {serializer.errors}"

    # Test with regular user (should be invalid)
    serializer = ContractChangeCreateUpdateSerializer(
        data={**contract_change_data, "executor": {"id": regular_user.id}}
    )
    assert not serializer.is_valid()
    assert "executor" in serializer.errors

    # Test with null executor (should be valid as `allow_null=True`)
    serializer = ContractChangeCreateUpdateSerializer(
        data={**contract_change_data, "executor": None}
    )
    assert serializer.is_valid(), f"Validation errors: {serializer.errors}"
