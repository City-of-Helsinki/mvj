from auditlog.context import set_actor
from auditlog.middleware import AuditlogMiddleware
from django.utils.functional import SimpleLazyObject


class CustomAuditlogMiddleware(AuditlogMiddleware):
    def __call__(self, request):
        remote_addr = self._get_remote_addr(request)

        user = SimpleLazyObject(lambda: getattr(request, "user", None))

        context = set_actor(actor=user, remote_addr=remote_addr)

        with context:
            return self.get_response(request)