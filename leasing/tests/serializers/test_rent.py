import pytest
from rest_framework.exceptions import ValidationError

from leasing.enums import RentType
from leasing.models import Rent
from leasing.serializers.rent import RentCreateUpdateSerializer


@pytest.fixture
def rent_types_with_override() -> list[str]:
    """These rent types can use the rent override receivabletype during invoicing."""
    return [
        RentType.FIXED,
        RentType.INDEX,
        RentType.INDEX2022,
        RentType.MANUAL,
    ]


@pytest.fixture
def rent_types_without_override() -> list[str]:
    """These rent types do not use the rent override receivabletype during invoicing."""
    return [RentType.FREE, RentType.ONE_TIME]


@pytest.fixture
def rent_without_override_receivable_type(
    service_unit_factory,
    lease_factory,
    rent_factory,
) -> Rent:
    """
    Test data fixture for a rent with a lease and service unit that doesn't use
    the override receivabletype feature.
    """
    service_unit_without_override = service_unit_factory(
        name="Service unit without rent override receivabletype",
        use_rent_override_receivable_type=False,
    )
    lease_from_unit_without_override = lease_factory(
        service_unit=service_unit_without_override,
    )
    return rent_factory(lease=lease_from_unit_without_override)


@pytest.fixture
def rent_with_override_receivable_type(
    service_unit_factory,
    lease_factory,
    rent_factory,
) -> Rent:
    """
    Test data fixture for a rent with a lease and service unit that uses the
    override receivabletype feature.
    """
    service_unit_with_override = service_unit_factory(
        name="Service unit with rent override receivabletype",
        use_rent_override_receivable_type=True,
    )
    lease_from_unit_with_override = lease_factory(
        service_unit=service_unit_with_override,
    )
    return rent_factory(lease=lease_from_unit_with_override)


@pytest.mark.django_db
def test_validate_override_receivable_type_invalid_service_unit(
    receivable_type_factory,
    rent_without_override_receivable_type,
):
    """
    RentCreateUpdateSerializer should reject receivable types from service units
    that don't use override receivabletype, regardless of rent type.
    """
    serializer = RentCreateUpdateSerializer()
    rent_datas_invalid_service_unit = [
        {
            "type": rent_type,
            "override_receivable_type": receivable_type_factory(
                service_unit=rent_without_override_receivable_type.lease.service_unit
            ),
        }
        for rent_type in RentType
    ]
    for data in rent_datas_invalid_service_unit:
        # Input without a rent ID (e.g. during create)
        with pytest.raises(ValidationError):
            serializer.validate(data)

        # Input with a rent ID (e.g. during update)
        data["id"] = rent_without_override_receivable_type.id
        with pytest.raises(ValidationError):
            serializer.validate(data)


@pytest.mark.django_db
def test_validate_override_receivable_type_valid_inputs(
    receivable_type_factory,
    rent_with_override_receivable_type,
    rent_types_with_override,
):
    """
    RentCreateUpdateSerializer should allow override receivabletype from service
    units that use the feature, if rent type is valid.
    """
    serializer = RentCreateUpdateSerializer()
    rent_datas_valid_types_valid_unit = [
        {
            "type": rent_type,
            "override_receivable_type": receivable_type_factory(
                service_unit=rent_with_override_receivable_type.lease.service_unit
            ),
        }
        for rent_type in rent_types_with_override
    ]
    for data in rent_datas_valid_types_valid_unit:
        # Input without a rent ID (e.g. during create)
        assert serializer.validate(data)

        # Input with a rent ID (e.g. during update)
        data["id"] = rent_with_override_receivable_type.id
        assert serializer.validate(data)


@pytest.mark.django_db
def test_validate_override_receivable_type_lacking_inputs():
    """
    RentCreateUpdateSerializer should allow empty override receivable type
    input, when no additional details are known about the service unit or
    receivable type.

    This is the case for example when creating new rents with rent types that
    don't utilize the rent override receivabletype feature.
    """
    serializer = RentCreateUpdateSerializer()
    rent_datas_without_override_or_rent_id = [
        {
            "type": rent_type,
            "override_receivable_type": None,
        }
        for rent_type in RentType
    ]
    for data in rent_datas_without_override_or_rent_id:
        assert serializer.validate(data)


@pytest.mark.django_db
def test_validate_override_receivable_type_missing_receivabletype(
    rent_with_override_receivable_type,
    rent_types_with_override,
):
    """
    RentCreateUpdateSerializer should reject the input when service unit and
    rent types require override receivabletype, but it was not supplied, and
    the rent ID is known.

    The expected case is during an update of existing rent.
    During create, rent ID would not be known in validation.
    """
    serializer = RentCreateUpdateSerializer()
    rent_datas_valid_types_valid_unit_existing_rent_no_override = [
        {
            "id": rent_with_override_receivable_type.id,
            "type": rent_type,
            "override_receivable_type": None,
        }
        for rent_type in rent_types_with_override
    ]
    for data in rent_datas_valid_types_valid_unit_existing_rent_no_override:
        with pytest.raises(ValidationError):
            serializer.validate(data)


@pytest.mark.django_db
def test_validate_override_receivable_type_invalid_rent_type(
    receivable_type_factory,
    rent_with_override_receivable_type,
    rent_without_override_receivable_type,
    rent_types_without_override,
):
    """
    RentCreateUpdateSerializer should reject the input when rent type doesn't
    use override receivabletype in invoicing, but it was supplied.
    """
    serializer = RentCreateUpdateSerializer()
    rent_datas_invalid_types_invalid_unit = [
        {
            "type": rent_type,
            "override_receivable_type": receivable_type_factory(
                service_unit=rent_without_override_receivable_type.lease.service_unit
            ),
        }
        for rent_type in rent_types_without_override
    ]
    for data in rent_datas_invalid_types_invalid_unit:
        # Flow without rent ID
        with pytest.raises(ValidationError):
            serializer.validate(data)

        # Flow with rent ID
        data["id"] = rent_without_override_receivable_type.id
        with pytest.raises(ValidationError):
            serializer.validate(data)

    rent_datas_invalid_types_valid_unit = [
        {
            "type": rent_type,
            "override_receivable_type": receivable_type_factory(
                service_unit=rent_with_override_receivable_type.lease.service_unit
            ),
        }
        for rent_type in rent_types_without_override
    ]
    for data in rent_datas_invalid_types_valid_unit:
        # Flow without rent ID
        with pytest.raises(ValidationError):
            serializer.validate(data)

        # Flow with rent ID
        data["id"] = rent_with_override_receivable_type.id
        with pytest.raises(ValidationError):
            serializer.validate(data)
