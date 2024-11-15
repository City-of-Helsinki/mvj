import pytest
from rest_framework.exceptions import ValidationError

from leasing.enums import RentType, ServiceUnitId
from leasing.models import ServiceUnit
from leasing.serializers.rent import RentCreateUpdateSerializer


@pytest.mark.django_db
def test_is_valid_override_receivable_type(django_db_setup, receivable_type_factory):
    """
    Test that the requirements described in the target function docstring hold.
    """
    make = ServiceUnit.objects.get(pk=ServiceUnitId.MAKE)
    akv = ServiceUnit.objects.get(pk=ServiceUnitId.AKV)
    kuva_lipa = ServiceUnit.objects.get(pk=ServiceUnitId.KUVA_LIPA)
    kuva_upa = ServiceUnit.objects.get(pk=ServiceUnitId.KUVA_UPA)
    kuva_nup = ServiceUnit.objects.get(pk=ServiceUnitId.KUVA_NUP)

    serializer = RentCreateUpdateSerializer()

    # Validator should reject all MaKe receivable types regardless of rent type.
    rent_datas_make = [
        {
            "type": rent_type,
            "override_receivable_type": receivable_type_factory(service_unit=make),
        }
        for rent_type in RentType
    ]
    for data in rent_datas_make:
        with pytest.raises(ValidationError):
            serializer.validate(data)

    # Validator should allow empty override receivable type input.
    rent_datas_empty = [
        {
            "type": rent_type,
            "override_receivable_type": None,
        }
        for rent_type in RentType
    ]
    for data in rent_datas_empty:
        assert serializer.validate(data)

    # Validator should allow AKV and KuVa receivable types, if rent type is valid.
    rent_datas_akv_and_kuva = [
        {
            "type": RentType.INDEX2022,
            "override_receivable_type": receivable_type_factory(service_unit=unit),
        }
        for unit in [akv, kuva_lipa, kuva_upa, kuva_nup]
    ]
    for data in rent_datas_akv_and_kuva:
        assert serializer.validate(data)

    # Validator should allow rent types that can generate automatic invoices.
    rent_datas_valid_types = [
        {
            "type": rent_type,
            "override_receivable_type": receivable_type_factory(service_unit=akv),
        }
        for rent_type in [
            RentType.FIXED,
            RentType.INDEX,
            RentType.INDEX2022,
            RentType.MANUAL,
        ]
    ]
    for data in rent_datas_valid_types:
        assert serializer.validate(data)

    # Validator should reject the receivable type input for rent types that
    # don't generate automatic invoices.
    rent_datas_invalid_types = [
        {
            "type": rent_type,
            "override_receivable_type": receivable_type_factory(service_unit=akv),
        }
        for rent_type in [RentType.FREE, RentType.ONE_TIME]
    ]
    for data in rent_datas_invalid_types:
        with pytest.raises(ValidationError):
            serializer.validate(data)
