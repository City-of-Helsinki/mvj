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
from landuse.views.operations import InvoicePermission, PaymentSchedulePermission
from utils.group_permissions import UG

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


@pytest.mark.parametrize(
    "permission_class", [PaymentSchedulePermission, InvoicePermission]
)
def test_operation_permissions_deny_unrecognized_actions(
    permission_class, rf, user_factory
):
    request = rf.post("/")
    request.user = user_factory(is_superuser=True)
    view = type("View", (), {"action": "unrecognized_action"})()

    assert permission_class().has_permission(request, view) is False


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


def test_billing_role_can_reject_but_cannot_edit_schedule(client, tab_role_user):
    schedule, _ = create_agreement_financial_data()
    user = tab_role_user(UG.LASKUTTAJA)
    client.force_login(user)
    url = reverse("v1:landuse:payment-schedule-reject", args=(schedule.pk,))
    assert client.post(url, {"reason": ""}).status_code == status.HTTP_400_BAD_REQUEST
    schedule.refresh_from_db()
    assert schedule.status == PaymentScheduleStatus.PENDING_APPROVAL
    response = client.post(url, {"reason": "Incorrect amount"})
    assert response.status_code == status.HTTP_200_OK
    schedule.refresh_from_db()
    assert schedule.status == PaymentScheduleStatus.REJECTED
    assert schedule.rejected_reason == "Incorrect amount"
    response = client.put(
        reverse(
            "v1:landuse:agreement-payment-schedules", args=(schedule.agreement_id,)
        ),
        [],
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert PaymentSchedule.objects.filter(pk=schedule.pk).exists()


@pytest.mark.parametrize("operation", ["approve", "reject"])
def test_schedule_change_permission_does_not_authorize_approval(
    client, user_factory, operation
):
    schedule, _ = create_agreement_financial_data()
    user = user_factory(is_superuser=False)
    user.user_permissions.add(get_landuse_permission("change_tab_payment_schedules"))
    client.force_login(user)
    response = client.post(
        reverse(f"v1:landuse:payment-schedule-{operation}", args=(schedule.pk,)),
        {"reason": "Not authorized"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    schedule.refresh_from_db()
    assert schedule.status == PaymentScheduleStatus.PENDING_APPROVAL


@pytest.mark.parametrize(
    "role", [UG.VALMISTELIJA, UG.SOPIMUSVALMISTELIJA, UG.LASKUTTAJA, UG.PAAKAYTTAJA]
)
def test_operation_reads_use_tab_permissions(client, tab_role_user, role):
    schedule, invoice = create_agreement_financial_data()
    client.force_login(tab_role_user(role))
    for resource, instance in [("payment-schedule", schedule), ("invoice", invoice)]:
        assert (
            client.get(reverse(f"v1:landuse:{resource}-list")).status_code
            == status.HTTP_200_OK
        )
        assert (
            client.get(
                reverse(f"v1:landuse:{resource}-detail", args=(instance.pk,))
            ).status_code
            == status.HTTP_200_OK
        )


@pytest.mark.parametrize(
    "role", [UG.VALMISTELIJA, UG.SOPIMUSVALMISTELIJA, UG.LASKUTTAJA, UG.PAAKAYTTAJA]
)
def test_schedule_submission_uses_tab_change_permission(client, tab_role_user, role):
    schedule, _ = create_agreement_financial_data()
    schedule.status = PaymentScheduleStatus.DRAFT
    schedule.save()
    client.force_login(tab_role_user(role))
    response = client.post(
        reverse("v1:landuse:payment-schedule-submit", args=(schedule.pk,))
    )
    allowed = role in (UG.VALMISTELIJA, UG.PAAKAYTTAJA)
    assert response.status_code == (
        status.HTTP_200_OK if allowed else status.HTTP_403_FORBIDDEN
    )
    schedule.refresh_from_db()
    assert schedule.status == (
        PaymentScheduleStatus.PENDING_APPROVAL
        if allowed
        else PaymentScheduleStatus.DRAFT
    )
