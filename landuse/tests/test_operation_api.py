from unittest.mock import patch

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from rest_framework import status

from landuse.models.agreement import LandUseAgreement
from landuse.models.contract import Contract
from landuse.models.invoice import Invoice
from landuse.models.party import AgreementParty
from landuse.models.payment_schedule import PaymentSchedule, PaymentScheduleStatus

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def enable_landuse_api(settings):
    settings.FLAG_LANDUSE_API_ENABLED = True
    settings.SAP_LANDUSE_VALUES = {
        "sender_id": "1111",
        "sales_org": "2222",
    }


def create_agreement_financial_data():
    agreement = LandUseAgreement.objects.create(identifier="M-2026-1")
    party = AgreementParty.objects.create(agreement=agreement)
    contract = Contract.objects.create(agreement=agreement)
    schedule = PaymentSchedule.objects.create(
        agreement=agreement,
        recipient_party=party,
        contract=contract,
        status=PaymentScheduleStatus.PENDING_APPROVAL,
    )
    invoice = Invoice.objects.create(
        agreement=agreement,
        recipient_party=party,
        installment_sequence_number=1,
        installment_count_total=1,
        invoice_identifier="INV-1",
    )
    return schedule, invoice


def get_landuse_permission(codename):
    return Permission.objects.get(content_type__app_label="landuse", codename=codename)


def clear_permission_cache(user):
    for attribute in ("_perm_cache", "_user_perm_cache", "_group_perm_cache"):
        user.__dict__.pop(attribute, None)


def test_approve_payment_schedule_requires_operation_permission(client, user_factory):
    schedule, _ = create_agreement_financial_data()
    user = user_factory()
    user.user_permissions.add(get_landuse_permission("view_paymentschedule"))
    client.force_login(user)
    url = reverse("v1:landuse:payment-schedule-approve", args=(schedule.pk,))

    forbidden_response = client.post(url)
    user.user_permissions.add(get_landuse_permission("approve_paymentschedule"))
    clear_permission_cache(user)
    allowed_response = client.post(url)

    assert forbidden_response.status_code == status.HTTP_403_FORBIDDEN
    assert allowed_response.status_code == status.HTTP_200_OK
    schedule.refresh_from_db()
    assert schedule.status == PaymentScheduleStatus.APPROVED


@patch("landuse.models.invoice.send_invoice_xml")
def test_send_invoice_to_sap_requires_operation_permission(
    send_invoice_xml, client, user_factory
):
    _, invoice = create_agreement_financial_data()
    user = user_factory()
    user.user_permissions.add(get_landuse_permission("view_invoice"))
    client.force_login(user)
    url = reverse("v1:landuse:invoice-send-to-sap", args=(invoice.pk,))

    forbidden_response = client.post(url)
    user.user_permissions.add(get_landuse_permission("send_invoice_to_sap"))
    clear_permission_cache(user)
    allowed_response = client.post(url)

    assert forbidden_response.status_code == status.HTTP_403_FORBIDDEN
    assert allowed_response.status_code == status.HTTP_200_OK
    send_invoice_xml.assert_called_once()
    invoice.refresh_from_db()
    assert invoice.sent_at is not None
