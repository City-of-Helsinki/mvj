from rest_framework import status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from leasing.enums import LeaseState
from leasing.filters import ApplicationFilter, DecisionFilter, LeaseFilter, RentFilter, TenantFilter
from leasing.models import Decision, Rent, Tenant
from leasing.serializers import (
    ApplicationSerializer, ContactSerializer, DecisionSerializer, LeaseCreateUpdateSerializer, LeaseSerializer,
    RentSerializer, TenantCreateUpdateSerializer, TenantSerializer)

from .models import Application, Contact, Lease


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    filter_class = ApplicationFilter

    @detail_route(methods=['post'])
    def create_lease(self, request, pk=None):
        """Create a new Lease instance from an application.

        Preparer is set as the current user. The contact details on the
        application will be added as a new Contact. The new contact is added
        as a Tenant to the Lease.
        """
        application = self.get_object()

        lease_data = {
            'application': application.id,
            'reasons': application.reasons,
            'preparer': request.user.id,
            'state': LeaseState.DRAFT
        }

        lease_serializer = LeaseCreateUpdateSerializer(data=lease_data)

        if lease_serializer.is_valid():
            lease = lease_serializer.save()
            contact = application.as_contact()
            contact.save()

            Tenant.objects.create(
                contact_id=contact.id,
                lease=lease,
                share=1
            )

            return Response(lease_serializer.data)
        else:
            return Response(lease_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DecisionViewSet(viewsets.ModelViewSet):
    queryset = Decision.objects.all()
    serializer_class = DecisionSerializer
    filter_class = DecisionFilter


class RentViewSet(viewsets.ModelViewSet):
    queryset = Rent.objects.all()
    serializer_class = RentSerializer
    filter_class = RentFilter


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
