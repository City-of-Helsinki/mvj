import django_filters

from leasing.enums import ApplicationState, ApplicationType, DecisionType, LeaseState, RentType
from leasing.models import Application, Decision, Lease, Rent, Tenant


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


class LeaseFilter(django_filters.rest_framework.FilterSet):
    application_id = django_filters.NumberFilter(name="application__id")
    preparer_id = django_filters.NumberFilter(name="preparer__id")
    state = django_filters.ChoiceFilter(choices=[(i.value, getattr(i, 'label', i.name)) for i in LeaseState])

    class Meta:
        model = Lease
        fields = ['application_id', 'is_reservation', 'lease_id', 'preparer_id', 'state']


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
