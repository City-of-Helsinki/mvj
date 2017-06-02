from xml.dom import minidom
from xml.etree import ElementTree

import requests
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseServerError, StreamingHttpResponse
from requests.auth import HTTPBasicAuth
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, detail_route, list_route, permission_classes
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_gis.filters import InBBoxFilter

from leasing.enums import LeaseState
from leasing.filters import (
    ApplicationFilter, DecisionFilter, InvoiceFilter, LeaseFilter, NoteFilter, RentFilter, TenantFilter)
from leasing.models import Area, Decision, Invoice, Note, Rent, Tenant
from leasing.serializers import (
    ApplicationSerializer, AreaSerializer, ContactSerializer, DecisionSerializer, InvoiceSerializer,
    LeaseCreateUpdateSerializer, LeaseSerializer, NoteSerializer, RentSerializer, TenantCreateUpdateSerializer,
    TenantSerializer)

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


class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    filter_backends = (SearchFilter, InBBoxFilter)
    search_fields = ('name', )
    bbox_filter_field = 'mpoly'
    bbox_filter_include_overlapping = True


class DecisionViewSet(viewsets.ModelViewSet):
    queryset = Decision.objects.all()
    serializer_class = DecisionSerializer
    filter_class = DecisionFilter


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    filter_class = InvoiceFilter

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def create_invoices(self, request, pk=None):
        """Runs the create_invoices management command"""
        from django.core.management import call_command

        call_command('create_invoices')

        return Response()

    @list_route(permission_classes=[IsAuthenticated])
    def laske_xml(self, request, pk=None):
        root = ElementTree.Element('SBO_SalesOrders')

        for invoice in Invoice.objects.order_by('-created_at'):
            root.append(invoice.as_laske_xml())

        xml_string = ElementTree.tostring(root)

        return HttpResponse(minidom.parseString(xml_string).toprettyxml(), content_type='text/xml')


class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    filter_class = NoteFilter
    search_fields = ('title', 'text')


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
    queryset = Lease.objects.all().select_related('application', 'identifier', 'preparer')
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


@api_view()
@permission_classes([IsAuthenticated])
def ktj_proxy(request, base_type, print_type):
    required_settings = ('KTJ_PRINT_ROOT_URL', 'KTJ_PRINT_USERNAME', 'KTJ_PRINT_PASSWORD')

    for required_setting in required_settings:
        if not hasattr(settings, required_setting) or not getattr(settings, required_setting):
            return HttpResponseServerError("Please set {} setting".format(required_setting))

    allowed_types = [
        'kiinteistorekisteriote_oik_tod/rekisteriyksikko',
        'kiinteistorekisteriote_oik_tod/maaraala',
        'kiinteistorekisteriote/rekisteriyksikko',
        'kiinteistorekisteriote/maaraala',
        'lainhuutotodistus_oik_tod',
        'lainhuutotodistus',
        'rasitustodistus_oik_tod',
        'rasitustodistus',
        'vuokraoikeustodistus_oik_tod',
        'vuokraoikeustodistus',
        'muodostumisketju_eteenpain',
        'muodostumisketju_taaksepain',
        'voimassa_olevat_muodostuneet',
        'muodostajarekisteriyksikot_ajankohtana',
        'muodostajaselvitys',
        'yhteystiedot',
        'ktjote_oik_tod/kayttooikeusyksikko',
        'ktjote/kayttooikeusyksikko',
    ]

    allowed_params = [
        'kiinteistotunnus',
        'maaraalatunnus',
        'kohdetunnus',
        'lang',
        'leikkauspvm',
    ]

    if print_type not in allowed_types:
        raise Http404

    url = '{}/{}/tuloste/{}/pdf'.format(settings.KTJ_PRINT_ROOT_URL, base_type, print_type)
    params = request.GET.copy()

    for param in request.GET:
        if param not in allowed_params:
            del params[param]

    r = requests.get(url, data=params, auth=HTTPBasicAuth(settings.KTJ_PRINT_USERNAME, settings.KTJ_PRINT_PASSWORD),
                     stream=True)

    return StreamingHttpResponse(status=r.status_code, reason=r.reason, content_type=r.headers['Content-Type'],
                                 streaming_content=r.raw)
