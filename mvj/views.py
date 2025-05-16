import logging
from typing import Literal

from django.apps import apps
from django.core.exceptions import AppRegistryNotReady
from django.db import DatabaseError, connection
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
from rest_framework import status

logger = logging.getLogger(__name__)


def _app_is_ready() -> bool:
    try:
        apps.check_apps_ready()
        apps.check_models_ready()
        return True
    except AppRegistryNotReady:
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking app readiness: {e}")
        return False


def _database_is_ready() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
            if row is None:
                raise DatabaseError("Unable to fetch from database")
            return True
    except DatabaseError:
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking database readiness: {e}")
        return False


@require_GET
def healthz(*args, **kwargs):
    return HttpResponse(status=status.HTTP_200_OK)


@require_GET
def readiness(*args, **kwargs):
    readiness_status = {
        "database": _database_is_ready(),
        "application": _app_is_ready(),
    }
    if all(readiness_status.values()):
        return JsonResponse({"status": "ready"}, status=status.HTTP_200_OK)

    not_ready_components: list[Literal["database", "application"]] = [
        k for k, v in readiness_status.items() if not v
    ]
    return JsonResponse(
        {"status": f"not ready: {','.join(not_ready_components)}"},
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )
