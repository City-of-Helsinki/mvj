from auditlog.middleware import AuditlogMiddleware
from django.db import transaction
from rest_framework import viewsets


class AuditLogMixin:
    def initial(self, request, *args, **kwargs):
        # We need to process logged in user again because Django Rest
        # Framework handles authentication after the
        # AuditLogMiddleware.
        AuditlogMiddleware().process_request(request)
        return super().initial(request, *args, **kwargs)


class AtomicTransactionMixin:
    @transaction.atomic
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class AtomicTransactionModelViewSet(AtomicTransactionMixin, viewsets.ModelViewSet):
    """Viewset that combines AtomicTransactionMixin and rest_framework.viewsets.ModelViewSet"""
