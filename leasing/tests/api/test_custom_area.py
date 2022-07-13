import json

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.reverse import reverse

from leasing.models.land_area import CustomArea, UtilDistribution


@pytest.mark.django_db
def test_create_lease(django_db_setup, admin_client, custom_area_in_lease):
    url = reverse("lease-list")
    response = admin_client.post(
        url,
        data=json.dumps(custom_area_in_lease, cls=DjangoJSONEncoder),
        content_type="application/json",
    )
    assert response.status_code == 201
    response = admin_client.get(url)
    assert response.status_code == 200
    assert len(CustomArea.objects.all()) == 1
    assert len(UtilDistribution.objects.all()) == 1
    assert len(CustomArea.objects.filter(identifier="54321")) == 1
    url = reverse("lease-detail", kwargs={"pk": response.json()["results"][0]["id"]})
    custom_area_in_lease["lease_areas"][0]["custom_area"][
        "rent_build_permission"
    ] = 4000
    response = admin_client.patch(
        url,
        data=json.dumps(custom_area_in_lease, cls=DjangoJSONEncoder),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert CustomArea.objects.all().last().rent_build_permission == 4000
