from multiprocessing import Event, Value

import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.urls import reverse
from django_q.brokers import get_broker
from django_q.cluster import monitor, pusher, worker
from django_q.queues import Queue
from django_q.tasks import queue_size

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
