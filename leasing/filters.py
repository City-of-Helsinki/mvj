import django_filters

from leasing.enums import (
    LEASE_IDENTIFIER_DISTRICT, LEASE_IDENTIFIER_MUNICIPALITY, LEASE_IDENTIFIER_TYPE, ApplicationState, ApplicationType,
    DecisionType, InvoiceState, LeaseState, RentType)
from leasing.models import Application, Decision, Invoice, Lease, Note, Rent, Tenant


class ApplicationFilter(django_filters.rest_framework.FilterSet):
    state = django_filters.ChoiceFilter(choices=[(i.value, getattr(i, 'label', i.name)) for i in ApplicationState])
    type = django_filters.ChoiceFilter(choices=[(i.value, getattr(i, 'label', i.name)) for i in ApplicationType])

    class Meta:
        model = Application
        fields = ['state', 'is_open', 'type']


class DecisionFilter(django_filters.rest_framework.FilterSet):
    type = django_filters.ChoiceFilter(choices=[(i.value, getattr(i, 'label', i.name)) for i in DecisionType])
    added_by_id = django_filters.NumberFilter(name="added_by__id")

    class Meta:
        model = Decision
        fields = ['lease', 'type', 'added_by_id']


class InvoiceFilter(django_filters.rest_framework.FilterSet):
    state = django_filters.ChoiceFilter(choices=[(i.value, getattr(i, 'label', i.name)) for i in InvoiceState])
    contact_id = django_filters.NumberFilter(name="tenants__contact__id")
    tenant_id = django_filters.NumberFilter(name="tenants__id")
    lease_id = django_filters.NumberFilter(name="tenants__lease__id")

    class Meta:
        model = Invoice
        fields = ['contact_id', 'tenant_id', 'lease_id']


class LeaseFilter(django_filters.rest_framework.FilterSet):
    application_id = django_filters.NumberFilter(name="application__id")
    preparer_id = django_filters.NumberFilter(name="preparer__id")
    state = django_filters.ChoiceFilter(choices=[(i.value, getattr(i, 'label', i.name)) for i in LeaseState])
    identifier_type = django_filters.ChoiceFilter(choices=LEASE_IDENTIFIER_TYPE)
    identifier_municipality = django_filters.ChoiceFilter(choices=LEASE_IDENTIFIER_MUNICIPALITY)
    identifier_district = django_filters.ChoiceFilter(choices=LEASE_IDENTIFIER_DISTRICT)

    class Meta:
        model = Lease
        fields = ['application_id', 'is_reservation', 'identifier', 'preparer_id', 'state']


class NoteFilter(django_filters.rest_framework.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    text = django_filters.CharFilter(lookup_expr='icontains')
    author = django_filters.NumberFilter(name="author__id")
    application_id = django_filters.NumberFilter(label="Application ID", name="application__id")
    area_id = django_filters.NumberFilter(label="Area ID", name="area__id")
    lease_id = django_filters.NumberFilter(label="Lease ID", name="lease__id")

    class Meta:
        model = Note
        fields = ['title', 'text', 'author', 'application_id', 'area_id', 'lease_id']


class RentFilter(django_filters.rest_framework.FilterSet):
    type = django_filters.ChoiceFilter(choices=[(i.value, getattr(i, 'label', i.name)) for i in RentType])

    class Meta:
        model = Rent
        fields = ['lease', 'type']


class TenantFilter(django_filters.rest_framework.FilterSet):
    contact_id = django_filters.NumberFilter(name="contact__id")
    contact_contact_id = django_filters.NumberFilter(name="contact_contact__id")
    billing_contact_id = django_filters.NumberFilter(name="billing_contact__id")

    class Meta:
        model = Tenant
        fields = ['lease', 'contact_id', 'contact_contact_id', 'billing_contact_id']
