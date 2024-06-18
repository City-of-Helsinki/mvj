from datetime import datetime
from multiprocessing import Event, Value
from unittest.mock import patch

import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.urls import reverse
from django.utils.timezone import make_aware, now
from django_q.brokers import get_broker
from django_q.cluster import monitor, pusher, worker
from django_q.queues import Queue
from django_q.tasks import queue_size

from leasing.enums import DueDatesType, InvoiceState
from leasing.report.invoice.laske_invoice_count_report import LaskeInvoiceCountReport
from leasing.report.lease.lease_statistic_report import LeaseStatisticReport
from leasing.report.viewset import ENABLED_REPORTS


def _add_report_permission(user, reports):
    report_content_type, created = ContentType.objects.get_or_create(
        app_label="leasing", model="report"
    )

    if not isinstance(reports, list):
        reports = [reports]

    for report in reports:
        codename = "can_generate_report_{}".format(report.slug)
        permission, created = Permission.objects.get_or_create(
            name=codename,
            codename=codename,
            content_type=report_content_type,
        )

        user.user_permissions.add(permission)


@pytest.fixture(autouse=True)
def use_q_cluster_testing(settings):
    settings.Q_CLUSTER = {
        "name": "DjangORM",
        "cpu_affinity": 1,
        "testing": True,
        "log_level": "DEBUG",
        "orm": "default",
    }


@pytest.mark.django_db(transaction=True)
def test_simple_async_report_send(rf, admin_user):
    broker = get_broker()
    assert broker.queue_size() == 0

    request = rf.get("/")
    request.query_params = {}
    request.user = admin_user

    report = LeaseStatisticReport()
    response = report.get_response(request)
    assert response.data
    assert broker.queue_size() == 1

    # Run async task
    task_queue = Queue()
    result_queue = Queue()
    event = Event()
    event.set()
    pusher(task_queue, event, broker=broker)
    assert task_queue.qsize() == 1
    assert queue_size(broker=broker) == 0
    task_queue.put("STOP")
    worker(task_queue, result_queue, Value("f", -1))
    assert task_queue.qsize() == 0
    assert result_queue.qsize() == 1
    result_queue.put("STOP")
    monitor(result_queue)
    assert result_queue.qsize() == 0
    broker.delete_queue()

    # Test report file have been sent via email
    assert len(mail.outbox) == 1
    assert len(mail.outbox[0].attachments) == 1


@pytest.mark.django_db
@pytest.mark.parametrize("report", ENABLED_REPORTS)
def test_report_options_respond_with_ok(admin_client, report):
    url = reverse("v1:report-detail", kwargs={"report_type": report.slug})

    response = admin_client.options(url)

    assert response.status_code == 200
    assert response.json() is not None


@pytest.mark.django_db
@pytest.mark.parametrize("report", ENABLED_REPORTS)
def test_can_generate_report_permission(client, user, report):
    client.force_login(user)

    url = reverse("v1:report-detail", kwargs={"report_type": report.slug})

    response = client.get(url)
    assert response.status_code == 403

    _add_report_permission(user, report)

    response = client.get(url)
    assert response.status_code == 200 or response.status_code == 400


@pytest.mark.django_db
def test_report_list(client, user):
    client.force_login(user)

    url = reverse("v1:report-list")

    response = client.get(url)
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 0

    _add_report_permission(user, ENABLED_REPORTS[-3:])

    response = client.get(url)
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 3

    assert {r.slug for r in ENABLED_REPORTS[-3:]} == set(data.keys())


@pytest.mark.django_db
def test_laske_invoice_count_report(
    client,
    user,
    invoice_factory,
    service_unit_factory,
    lease_factory,
    contact_factory,
    rent_factory,
):
    _add_report_permission(user, LaskeInvoiceCountReport)
    client.force_login(user)

    service_unit = service_unit_factory()
    lease = lease_factory(
        service_unit=service_unit, is_invoicing_enabled=True, end_date="2030-12-31"
    )
    contact = contact_factory()
    dates = [
        make_aware(datetime(2024, 6, 13)),
        make_aware(datetime(2024, 6, 14)),
        make_aware(datetime(2024, 6, 15)),
    ]
    for date in dates:
        invoice_factory.create(
            state=InvoiceState.OPEN,
            sent_to_sap_at=date,
            lease=lease,
            service_unit=service_unit,
            recipient=contact,
            total_amount=1000,
            billed_amount=1000,
        )

    # Create rent that should generate future invoices, to be listed in estimated_count
    rent_factory(
        lease=lease,
        start_date=make_aware(datetime(2024, 1, 1)),
        end_date=None,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=12,  # Monthly invoices, expected at the beginning of the month
    )
    # Create invoice in the future, to be listed in estimated_count
    invoice_factory(
        state=InvoiceState.OPEN,
        sent_to_sap_at=None,
        lease=lease,
        service_unit=service_unit,
        recipient=contact,
        total_amount=1000,
        billed_amount=1000,
        due_date=make_aware(datetime(2024, 7, 16)),
    )

    with patch("leasing.report.invoice.laske_invoice_count_report.now") as mock_now:
        # Freeze "today" to 2024-06-15 08:01:01 in django.utils.timezone.now() used in code
        mock_now.return_value = now().replace(
            year=2024, month=6, day=15, hour=8, minute=1, second=1
        )

        url = reverse(
            "v1:report-detail",
            kwargs={
                "report_type": LaskeInvoiceCountReport.slug,
            },
        )
        query_params = {
            "start_date": "2024-06-13",
            "end_date": "2024-08-18",
            "service_unit": service_unit.id,
        }
        response = client.get(url, data=query_params)

    assert response.status_code == 200

    response_data_dict = {
        item["send_date"].isoformat(): {
            "invoice_count": item["invoice_count"],
            "estimate_count": item["estimate_count"],
        }
        for item in response.data
    }

    assert response_data_dict == {
        "2024-06-13": {"invoice_count": 1, "estimate_count": 0},
        "2024-06-14": {"invoice_count": 1, "estimate_count": 0},
        "2024-06-15": {"invoice_count": 1, "estimate_count": 0},
        # Manually created invoice not yet sent to SAP
        "2024-06-16": {"invoice_count": 0, "estimate_count": 1},
        # Invoices coming from rent
        "2024-07-01": {"invoice_count": 0, "estimate_count": 1},
        "2024-08-01": {"invoice_count": 0, "estimate_count": 1},
    }
