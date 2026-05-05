import json

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse

from leasing.models import LeaseBasisOfRent


@pytest.mark.django_db
def test_patch_lease_basis_of_rent_children_not_deleted(
    django_db_setup,
    admin_client,
    lease_test_data,
    lease_basis_of_rent_factory,
    rent_intended_use_factory,
):
    """Children of a LeaseBasisOfRent (specifically mast) should not be deleted
    when the LeaseBasisOfRent is updated."""

    lease = lease_test_data["lease"]
    intended_use = rent_intended_use_factory()

    parent_basis = lease_basis_of_rent_factory(
        lease=lease,
        intended_use=intended_use,
        area=100,
        area_unit="m2",
    )
    child1 = lease_basis_of_rent_factory(
        lease=lease,
        parent=parent_basis,
        intended_use=intended_use,
        area=50,
        area_unit="m2",
    )
    child2 = lease_basis_of_rent_factory(
        lease=lease,
        parent=parent_basis,
        intended_use=intended_use,
        area=50,
        area_unit="m2",
    )

    url = reverse("v1:lease-detail", kwargs={"pk": lease.id})
    data = {
        "basis_of_rents": [
            {
                "id": parent_basis.id,
                "intended_use": intended_use.id,
                "area": "100.00",
                "area_unit": "m2",
                "children": [
                    {
                        "id": child1.id,
                        "intended_use": intended_use.id,
                        "area": "50.00",
                        "area_unit": "m2",
                    },
                    {
                        "id": child2.id,
                        "intended_use": intended_use.id,
                        "area": "50.00",
                        "area_unit": "m2",
                    },
                ],
            }
        ],
    }

    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    # Children must still exist (not soft-deleted) and their IDs match (not recreated).
    alive_children = LeaseBasisOfRent.objects.filter(parent=parent_basis)
    assert alive_children.count() == 2
    assert set(alive_children.values_list("id", flat=True)) == {child1.id, child2.id}
