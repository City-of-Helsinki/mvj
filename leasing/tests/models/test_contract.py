import pytest
from sequences import get_next_value

from leasing.models import Contract, ContractType


@pytest.mark.django_db
def test_contract_number_should_be_none_if_no_lease():
    contract = Contract.objects.create(type=ContractType.objects.get(pk=1))

    assert contract.contract_number is None


@pytest.mark.django_db
def test_contract_number_should_not_be_generated_if_no_sequence_name(lease):
    service_unit = lease.service_unit
    service_unit.contract_number_sequence_name = None
    service_unit.save()

    contract = Contract.objects.create(
        type=ContractType.objects.get(pk=1),
        lease=lease,
    )

    assert contract.contract_number is None


@pytest.mark.django_db
def test_contract_number_should_start_from_first_contract_number(lease):
    service_unit = lease.service_unit
    service_unit.contract_number_sequence_name = "test_sequence"
    service_unit.first_contract_number = 500
    service_unit.save()

    contract = Contract.objects.create(
        type=ContractType.objects.get(pk=1),
        lease=lease,
    )

    assert contract.contract_number == 500


@pytest.mark.django_db
def test_contract_number_should_start_from_one_if_first_number_not_set(lease):
    service_unit = lease.service_unit
    service_unit.contract_number_sequence_name = "test_sequence"
    service_unit.first_contract_number = None
    service_unit.save()

    contract = Contract.objects.create(
        type=ContractType.objects.get(pk=1),
        lease=lease,
    )

    assert contract.contract_number == 1


@pytest.mark.django_db
def test_contract_number_should_not_be_set_on_existing_contract(lease):
    service_unit = lease.service_unit
    service_unit.contract_number_sequence_name = "test_sequence"
    service_unit.save()

    contract = Contract.objects.create(
        id=1,
        type=ContractType.objects.get(pk=1),
        lease=lease,
        contract_number=None,
    )

    assert contract.contract_number is None


@pytest.mark.django_db
def test_contract_number_should_not_change_on_save_if_already_set(lease):
    contract = Contract.objects.create(
        type=ContractType.objects.get(pk=1),
        lease=lease,
        contract_number=123,
    )

    assert contract.contract_number == 123


@pytest.mark.django_db
def test_contract_number_should_use_existing_sequence(lease):
    sequence_name = "test_sequence"
    service_unit = lease.service_unit
    service_unit.contract_number_sequence_name = sequence_name
    service_unit.first_contract_number = 1
    service_unit.save()

    for i in range(5):
        get_next_value(sequence_name)

    contract = Contract.objects.create(
        type=ContractType.objects.get(pk=1),
        lease=lease,
    )

    assert contract.contract_number == 6
