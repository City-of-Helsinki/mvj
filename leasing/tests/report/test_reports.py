from multiprocessing import Event, Value

import pytest
from django.core import mail
from django_q.brokers import get_broker
from django_q.cluster import monitor, pusher, worker
from django_q.queues import Queue
from django_q.tasks import queue_size

from leasing.report.lease.lease_statistic_report import LeaseStatisticReport


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
