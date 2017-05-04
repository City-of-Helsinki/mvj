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


class NestedViewSetMixin:
    parent_field_name = None
    parent_model = None

    @property
    def parent_argument_name(self):
        return '{}_pk'.format(self.parent_field_name)

    @property
    def parent_filter_name(self):
        return '{}_id'.format(self.parent_field_name)

    def get_queryset(self):
        if self.parent_argument_name in self.kwargs:
            pk = self.kwargs[self.parent_argument_name]
            queryset = super().get_queryset().filter(**{self.parent_filter_name: pk})
        else:
            queryset = super().get_queryset()

        return queryset

    def perform_create(self, serializer):
        additional_params = {}

        if self.kwargs[self.parent_argument_name]:
            additional_params = {
                self.parent_field_name: self.parent_model.objects.get(pk=self.kwargs[self.parent_argument_name])
            }

        serializer.save(**additional_params)


class DecisionViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = Decision.objects.all()
    serializer_class = DecisionSerializer
    parent_field_name = 'lease'
    parent_model = Lease
    filter_class = DecisionFilter


class RentViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = Rent.objects.all()
    serializer_class = RentSerializer
    parent_field_name = 'lease'
    parent_model = Lease
    filter_fields = ['lease']


class TenantViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = Tenant.objects.all().select_related('contact', 'contact_contact', 'billing_contact')
    serializer_class = TenantSerializer
    parent_field_name = 'lease'
    parent_model = Lease
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
