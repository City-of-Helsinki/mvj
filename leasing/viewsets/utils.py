
from auditlog.middleware import AuditlogMiddleware


class AuditLogMixin:
    def initial(self, request, *args, **kwargs):
        # We need to process logged in user again because Django Rest
        # Framework handles authentication after the
        # AuditLogMiddleware.
        AuditlogMiddleware().process_request(request)
        return super().initial(request, *args, **kwargs)
