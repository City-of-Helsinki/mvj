import json
from io import BytesIO

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse

from leasing.models import InfillDevelopmentCompensation, InfillDevelopmentCompensationLease
from leasing.serializers.infill_development_compensation import InfillDevelopmentCompensationAttachmentSerializer


@pytest.mark.django_db
def test_upload_attachment(django_db_setup, admin_client, lease_test_data, user_factory):
    lease = lease_test_data['lease']
    user = user_factory(username='test_user')

    idc = InfillDevelopmentCompensation.objects.create(user=user)
    idcl = InfillDevelopmentCompensationLease.objects.create(lease=lease, infill_development_compensation=idc)

    assert idcl.attachments.count() == 0

    data = {
        "infill_development_compensation_lease": idcl.id,
    }

    url = reverse('infilldevelopmentcompensationattachment-list')

    dummy_file = BytesIO(b'dummy data')
    dummy_file.name = 'dummy_file.zip'

    response = admin_client.post(url, data={
        'data': json.dumps(data, cls=DjangoJSONEncoder),
        'file': dummy_file
    })

    assert response.status_code == 201, '%s %s' % (response.status_code, response.data)

    assert idcl.attachments.count() == 1
    assert idcl.attachments.first().uploader == response.wsgi_request.user


@pytest.mark.django_db
def test_download_attachment(django_db_setup, admin_client, client, lease_test_data, user_factory):
    lease = lease_test_data['lease']
    user = user_factory(username='test_user')
    user.set_password('test_password')
    user.save()

    idc = InfillDevelopmentCompensation.objects.create(user=user)
    idcl = InfillDevelopmentCompensationLease.objects.create(lease=lease, infill_development_compensation=idc)

    assert idcl.attachments.count() == 0

    data = {
        "infill_development_compensation_lease": idcl.id,
    }

    url = reverse('infilldevelopmentcompensationattachment-list')

    dummy_file = BytesIO(b'dummy data')
    dummy_file.name = 'dummy_file.zip'

    response = admin_client.post(url, data={
        'data': json.dumps(data, cls=DjangoJSONEncoder),
        'file': dummy_file
    })

    assert response.status_code == 201, '%s %s' % (response.status_code, response.data)
    assert idcl.attachments.count() == 1

    attachment = idcl.attachments.first()
    attachment_serializer = InfillDevelopmentCompensationAttachmentSerializer(attachment)

    url = attachment_serializer.get_file_url(attachment)

    # anonymous shouldn't have the permission to download the file
    response = client.get(url)
    assert response.status_code == 401, '%s %s' % (response.status_code, response.data)
    assert response.data['detail'].code == 'not_authenticated'

    # logged in user without permissions shouldn't have the permission to download the file
    client.login(username='test_user', password='test_password')
    response = client.get(url)

    assert response.status_code == 403, '%s %s' % (response.status_code, response.data)
    assert response.data['detail'].code == 'permission_denied'

    # admin client should have the permission to download the file
    response = admin_client.get(url)
    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)
    assert response.get('Content-Disposition').startswith('attachment; filename="dummy_file')
    assert response.content == b'dummy data'
