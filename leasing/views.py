from rest_framework import viewsets
from rest_framework.filters import SearchFilter

from leasing.filters import ApplicationFilter, DecisionFilter, LeaseFilter, TenantFilter
from leasing.models import Decision, Rent, Tenant
from leasing.serializers import (
    ApplicationSerializer, ContactSerializer, DecisionSerializer, LeaseCreateUpdateSerializer, LeaseSerializer,
    RentSerializer, TenantCreateUpdateSerializer, TenantSerializer)

from .models import Application, Contact, Lease


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    filter_class = ApplicationFilter


class DecisionViewSet(viewsets.ModelViewSet):
    queryset = Decision.objects.all()
    serializer_class = DecisionSerializer
    filter_class = DecisionFilter


class RentViewSet(viewsets.ModelViewSet):
    queryset = Rent.objects.all()
    serializer_class = RentSerializer
    filter_fields = ['lease']


class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all().select_related('contact', 'contact_contact', 'billing_contact')
    serializer_class = TenantSerializer
    filter_class = TenantFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return TenantCreateUpdateSerializer

        return TenantSerializer


class LeaseViewSet(viewsets.ModelViewSet):
    queryset = Lease.objects.all().select_related('application', 'preparer')
    serializer_class = LeaseSerializer
    filter_class = LeaseFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return LeaseCreateUpdateSerializer

        return LeaseSerializer


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('email', 'name', 'organization_name')
