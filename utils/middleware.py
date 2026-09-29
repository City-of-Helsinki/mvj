from typing import Callable

from auditlog.context import set_actor
from auditlog.middleware import AuditlogMiddleware
from django.http import HttpRequest, HttpResponseBase
from django.utils.functional import SimpleLazyObject


class CustomAuditlogMiddleware(AuditlogMiddleware):  # type: ignore[misc]
    get_response: Callable[[HttpRequest], HttpResponseBase]

    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        remote_addr = self._get_remote_addr(request)

        user = SimpleLazyObject(lambda: getattr(request, "user", None))

        context = set_actor(actor=user, remote_addr=remote_addr)

        with context:
            return self.get_response(request)
