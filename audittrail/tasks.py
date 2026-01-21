import logging

from django.conf import settings
from django.core import management
from django.core.cache import cache

logger = logging.getLogger(__name__)

LOCK_ID_AUDITLOG = "push_auditlogs_to_elasticsearch_lock"
LOCK_TIMEOUT_AUDITLOG = 60 * 15  # 15 minutes max runtime


def push_auditlogs_to_elasticsearch():
    """Push audit logs to Elasticsearch.

    Uses cache-based locking to prevent concurrent executions.
    Can be disabled via ENABLE_AUDITLOG_ELASTICSEARCH_SYNC setting.
    """

    if not getattr(settings, "ENABLE_AUDITLOG_ELASTICSEARCH_SYNC", False):
        logger.debug("Auditlog Elasticsearch sync is disabled. Skipping.")
        return

    # Acquire lock to ensure only one process is running this task at a time
    lock_acquired = cache.add(LOCK_ID_AUDITLOG, "true", LOCK_TIMEOUT_AUDITLOG)

    if not lock_acquired:
        logger.info(
            "Another instance of `push_auditlogs_to_elasticsearch`is already running. Skipping."
        )
        return

    try:
        # Command of `django-resilient-logger` to push unsent `django-auditlog` LogEntry objects
        management.call_command("submit_unsent_entries")
    finally:
        # Lock is released immediately when task completes normally
        cache.delete(LOCK_ID_AUDITLOG)
