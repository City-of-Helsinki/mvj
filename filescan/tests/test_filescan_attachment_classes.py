import json
from unittest.mock import patch

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.http import FileResponse
from django.test import override_settings
from django.test.client import Client
from django.urls import reverse
from rest_framework import status as http_status

from conftest import (
    DistrictFactory,
    InfillDevelopmentCompensationLeaseFactory,
    InspectionFactory,
    LeaseAreaFactory,
    LeaseFactory,
    MunicipalityFactory,
    TargetStatusFactory,
)
from filescan.enums import FileScanResult
from filescan.models import FileScanStatus, _scan_file_task
from forms.models.form import Attachment, Field
from leasing.enums import LandUseAgreementAttachmentType, LeaseAreaAttachmentType
from leasing.models import (
    InfillDevelopmentCompensationAttachment,
    InspectionAttachment,
    LandUseAgreement,
    LandUseAgreementAttachment,
    LeaseAreaAttachment,
)
from leasing.models.debt_collection import CollectionCourtDecision, CollectionLetter
from leasing.tests.conftest import (
    LandUseAgreementFactory,
    LandUseAgreementStatusFactory,
    LandUseAgreementTypeFactory,
)
from plotsearch.models.plot_search import AreaSearchAttachment, MeetingMemo

# Attachment classes, with their API routes
attachment_class_details = [
    (Attachment, "v1:attachment"),
    (AreaSearchAttachment, "v1:areasearchattachment"),
    (CollectionCourtDecision, "v1:collectioncourtdecision"),
    (CollectionLetter, "v1:collectionletter"),
    (
        InfillDevelopmentCompensationAttachment,
        "v1:infilldevelopmentcompensationattachment",
    ),
    (InspectionAttachment, "v1:inspectionattachment"),
    (LandUseAgreementAttachment, "v1:landuseagreementattachment"),
    (LeaseAreaAttachment, "v1:leaseareaattachment"),
    (MeetingMemo, "v1:meetingmemo"),
]


@override_settings(FLAG_FILE_SCAN=False)
@pytest.mark.parametrize("file_class, api_route_root", attachment_class_details)
def test_attachment_classes(
    django_db_setup,
    admin_client: Client,
    _attachment_test_data,
    _landuseagreementattachment_test_data,
    file_class: type[models.Model],
    api_route_root: str,
):
    """
    Test the entire file scanning process, starting from API request to
    create a new instance of an attachment class that utilizes file scanning,
    and verifying that downloads are allowed or denied when appropriate.
    """
    uploaded_file = SimpleUploadedFile(
        name="test_attachment.pdf", content=b"test", content_type="application/pdf"
    )

    with pytest.raises(FileScanStatus.DoesNotExist):
        # No FileScanStatuses should exist yet for this attachment model
        FileScanStatus.objects.get(
            content_type=ContentType.objects.get_for_model(file_class)
        )

    with override_settings(FLAG_FILE_SCAN=True):
        # Create one instance of the attachment class.
        # This is expected to create a corresponding FileScanStatus instance.
        with patch("filescan.models.async_task") as _:
            path = reverse(f"{api_route_root}-list")
            request_details = _get_request_details(
                file_class,
                uploaded_file,
                _attachment_test_data,
                _landuseagreementattachment_test_data,
            )
            response = admin_client.post(
                path,
                request_details,
            )
            assert response.status_code == 201

        attachment_id = response.data["id"]
        try:
            filescans = FileScanStatus.objects.filter(
                content_type=ContentType.objects.get_for_model(file_class),
                object_id=attachment_id,
            )
            assert filescans.count() == 1
        except FileScanStatus.DoesNotExist:
            pytest.fail()

        filescan = filescans.first()
        assert filescan is not None
        assert filescan.scan_result() == FileScanResult.PENDING

        # If file has not yet been scanned, deny download
        url_download = reverse(
            f"{api_route_root}-download", kwargs={"pk": attachment_id}
        )
        response = admin_client.get(path=url_download)
        assert response.status_code == http_status.HTTP_403_FORBIDDEN
        assert "error" in response.data.keys()

        # If a file has been scanned successfully with no detections, allow download
        _mock_scan_file_task_safe(filescan.pk)
        file_response: FileResponse = admin_client.get(path=url_download)
        uploaded_file.seek(0)
        assert file_response.status_code == 200
        assert b"".join(file_response.streaming_content) == uploaded_file.read()

        # If scanning process encountered an error, deny download
        _mock_scan_file_task_error(filescan.pk)
        response = admin_client.get(path=url_download)
        assert response.status_code == http_status.HTTP_403_FORBIDDEN
        assert "error" in response.data.keys()

        # If file was deleted due to detected virus, deny download
        _mock_scan_file_task_unsafe(filescan.pk)
        response = admin_client.get(path=url_download)
        assert response.status_code == http_status.HTTP_410_GONE
        assert "error" in response.data.keys()


def _get_request_details(
    file_class: type[models.Model],
    file: SimpleUploadedFile,
    attachment_test_data: Field,
    landuseagreementattachment_test_data: LandUseAgreement,
) -> dict:
    match file_class.__name__:
        case Attachment.__name__:
            return _get_attachment_request_details(file, attachment_test_data)

        case AreaSearchAttachment.__name__:
            return _get_areasearchattachment_request_details(file)

        case CollectionLetter.__name__ | CollectionCourtDecision.__name__:
            return _get_debtcollection_request_details(file)

        case InfillDevelopmentCompensationAttachment.__name__:
            return _get_infilldevelopment_request_details(file)

        case InspectionAttachment.__name__:
            return _get_inspectionattachment_request_details(file)

        case LandUseAgreementAttachment.__name__:
            return _get_landuseagreement_request_details(
                file, landuseagreementattachment_test_data
            )
        case LeaseAreaAttachment.__name__:
            return _get_leaseareaattachmment_request_details(file)

        case MeetingMemo.__name__:
            return _get_meetingmemo_request_details(file)

        case _:
            pytest.fail(f"POST payload not known for class {file_class.__name__}")


def _get_attachment_request_details(file: SimpleUploadedFile, field: Field) -> dict:
    return {"field": field.pk, "name": file.name, "attachment": file}


def _get_areasearchattachment_request_details(
    file: SimpleUploadedFile,
) -> dict:
    return {"name": file.name, "attachment": file}


def _get_debtcollection_request_details(
    file: SimpleUploadedFile,
) -> dict:
    """
    ViewSet uses a MultiPartJsonParser.
    """
    lease = LeaseFactory()
    return {
        "data": json.dumps(
            {
                "lease": lease.pk,
            }
        ),
        "file": file,
    }


def _get_infilldevelopment_request_details(
    file: SimpleUploadedFile,
) -> dict:
    """
    ViewSet uses a MultiPartJsonParser.
    """
    idc_lease = InfillDevelopmentCompensationLeaseFactory()
    return {
        "data": json.dumps(
            {
                "infill_development_compensation_lease": idc_lease.pk,
            }
        ),
        "file": file,
    }


def _get_inspectionattachment_request_details(
    file: SimpleUploadedFile,
) -> dict:
    """
    ViewSet uses a MultiPartJsonParser.
    """
    inspection = InspectionFactory()
    return {
        "data": json.dumps(
            {
                "inspection": inspection.pk,
            }
        ),
        "file": file,
    }


def _get_landuseagreement_request_details(
    file: SimpleUploadedFile, landuseagreement_test_data: LandUseAgreement
) -> dict:
    """
    ViewSet uses a MultiPartJsonParser.
    """
    attachment_type = LandUseAgreementAttachmentType.GENERAL.value
    return {
        "data": json.dumps(
            {
                "land_use_agreement": landuseagreement_test_data.pk,
                "type": attachment_type,
            }
        ),
        "file": file,
    }


def _get_leaseareaattachmment_request_details(
    file: SimpleUploadedFile,
) -> dict:
    """
    ViewSet uses a MultiPartJsonParser.
    """
    lease_area = LeaseAreaFactory()
    attachment_type = LeaseAreaAttachmentType.GEOTECHNICAL.value
    return {
        "data": json.dumps({"lease_area": lease_area.pk, "type": attachment_type}),
        "file": file,
    }


def _get_meetingmemo_request_details(file: SimpleUploadedFile) -> dict:
    target_status = TargetStatusFactory()
    return {"name": file.name, "meeting_memo": file, "target_status": target_status.pk}


def _mock_scan_file_task_safe(scan_status_id: int) -> None:
    """
    Run virus scan with a mocked response for a safe file.
    """
    with patch("filescan.models.requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "success": True,
            "data": {
                "result": [
                    {
                        "name": "something",
                        "is_infected": False,
                        "viruses": [],
                    }
                ]
            },
        }
        _scan_file_task(scan_status_id)


def _mock_scan_file_task_error(scan_status_id: int) -> None:
    """
    Run virus scan with a mocked response for a failed scan.
    """
    with patch("filescan.models.requests.post") as mock_post:
        mock_post.return_value.status_code = 500
        mock_post.return_value.json.return_value = {
            "success": False,
            "data": {},
        }
        _scan_file_task(scan_status_id)


def _mock_scan_file_task_unsafe(scan_status_id: int) -> None:
    """
    Run virus scan with a mocked response for an unsafe file.
    """
    with patch("filescan.models.requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "success": True,
            "data": {
                "result": [
                    {
                        "name": "something",
                        "is_infected": True,
                        "viruses": ["SomeVirus.exe"],
                    }
                ]
            },
        }
        _scan_file_task(scan_status_id)


@pytest.fixture
def _landuseagreementattachment_test_data() -> LandUseAgreement:
    """
    Minimal dependency setup for a LandUseAgreementAttachment.
    """
    municipality = MunicipalityFactory(name="Helsinki")
    district = DistrictFactory(
        name="TestDistrict", identifier=999, municipality=municipality
    )
    land_use_agreement_type = LandUseAgreementTypeFactory(name="Test type")
    land_use_agreement_status = LandUseAgreementStatusFactory(name="Test status")
    land_use_agreement = LandUseAgreementFactory(
        type_id=land_use_agreement_type.pk,
        municipality=municipality,
        district=district,
        status_id=land_use_agreement_status.pk,
    )
    return land_use_agreement


@pytest.fixture
def _attachment_test_data(form_factory, section_factory, field_factory) -> Field:
    """
    Minimal dependency setup for an Attachment.
    """
    form = form_factory(
        name="test name",
        description="test description",
        title="test form",
    )
    section = section_factory(
        form=form,
        title="test title",
        identifier="test-section",
    )
    field = field_factory(
        label="test label",
        section=section,
        type="textbox",
        identifier="test-field",
    )
    return field
