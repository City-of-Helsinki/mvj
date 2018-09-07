import datetime
import io
from decimal import Decimal
from itertools import groupby
from pathlib import Path

from dateutil import parser
from django.apps import apps
from django.db.models import DurationField
from django.db.models.functions import Cast
from django.http import HttpResponse
from docxtpl import DocxTemplate
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from leasing.filters import DistrictFilter, LeaseFilter
from leasing.models import (
    District, Financing, Hitas, IntendedUse, Lease, LeaseType, Management, Municipality, NoticePeriod, Regulation,
    RelatedLease, StatisticalUse, SupportiveHousing)
from leasing.models.utils import get_billing_periods_for_year
from leasing.serializers.explanation import ExplanationSerializer
from leasing.serializers.invoice import CreateChargeSerializer
from leasing.serializers.lease import (
    DistrictSerializer, FinancingSerializer, HitasSerializer, IntendedUseSerializer, LeaseCreateUpdateSerializer,
    LeaseListSerializer, LeaseRetrieveSerializer, LeaseSuccinctSerializer, LeaseTypeSerializer, ManagementSerializer,
    MunicipalitySerializer, NoticePeriodSerializer, RegulationSerializer, RelatedLeaseSerializer,
    StatisticalUseSerializer, SupportiveHousingSerializer)

from .utils import AtomicTransactionModelViewSet, AuditLogMixin


class DistrictViewSet(AtomicTransactionModelViewSet):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    filterset_class = DistrictFilter


class FinancingViewSet(AtomicTransactionModelViewSet):
    queryset = Financing.objects.all()
    serializer_class = FinancingSerializer


class HitasViewSet(AtomicTransactionModelViewSet):
    queryset = Hitas.objects.all()
    serializer_class = HitasSerializer


class IntendedUseViewSet(AtomicTransactionModelViewSet):
    queryset = IntendedUse.objects.all()
    serializer_class = IntendedUseSerializer


class LeaseTypeViewSet(AtomicTransactionModelViewSet):
    queryset = LeaseType.objects.all()
    serializer_class = LeaseTypeSerializer


class ManagementViewSet(AtomicTransactionModelViewSet):
    queryset = Management.objects.all()
    serializer_class = ManagementSerializer


class MunicipalityViewSet(AtomicTransactionModelViewSet):
    queryset = Municipality.objects.all()
    serializer_class = MunicipalitySerializer


class NoticePeriodViewSet(AtomicTransactionModelViewSet):
    queryset = NoticePeriod.objects.all().annotate(duration_as_interval=Cast('duration', DurationField())).order_by(
        'duration_as_interval')
    serializer_class = NoticePeriodSerializer


class RegulationViewSet(AtomicTransactionModelViewSet):
    queryset = Regulation.objects.all()
    serializer_class = RegulationSerializer


class StatisticalUseViewSet(AtomicTransactionModelViewSet):
    queryset = StatisticalUse.objects.all()
    serializer_class = StatisticalUseSerializer


class SupportiveHousingViewSet(AtomicTransactionModelViewSet):
    queryset = SupportiveHousing.objects.all()
    serializer_class = SupportiveHousingSerializer


class RelatedLeaseViewSet(AtomicTransactionModelViewSet):
    queryset = RelatedLease.objects.all()
    serializer_class = RelatedLeaseSerializer


class LeaseViewSet(AuditLogMixin, AtomicTransactionModelViewSet):
    serializer_class = LeaseRetrieveSerializer
    filterset_class = LeaseFilter

    def get_queryset(self):
        """Allow filtering leases by lease identifier

        `identifier` query parameter can be used to find the Lease with the provided identifier.
        example: .../lease/?identifier=S0120-219
        """
        identifier = self.request.query_params.get('identifier')
        succinct = self.request.query_params.get('succinct')

        if succinct:
            queryset = Lease.objects.succinct_select_related_and_prefetch_related()
        else:
            queryset = Lease.objects.full_select_related_and_prefetch_related()

        if identifier is not None:
            if len(identifier) < 3:
                queryset = queryset.filter(identifier__type__identifier__istartswith=identifier)
            elif len(identifier) == 3:
                queryset = queryset.filter(identifier__type__identifier__iexact=identifier[:2],
                                           identifier__municipality__identifier=identifier[2:3])
            elif len(identifier) < 7:
                district_identifier = identifier[3:5]
                if district_identifier == '0':
                    queryset = queryset.filter(identifier__type__identifier__iexact=identifier[:2],
                                               identifier__municipality__identifier=identifier[2:3],
                                               identifier__district__identifier__in=range(0, 10))
                else:
                    if district_identifier != '00':
                        district_identifier = district_identifier.lstrip('0')

                    queryset = queryset.filter(identifier__type__identifier__iexact=identifier[:2],
                                               identifier__municipality__identifier=identifier[2:3],
                                               identifier__district__identifier__startswith=district_identifier)
            else:
                queryset = queryset.filter(identifier__type__identifier__iexact=identifier[:2],
                                           identifier__municipality__identifier=identifier[2:3],
                                           identifier__district__identifier=identifier[3:5],
                                           identifier__sequence__startswith=identifier[6:])

        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update', 'metadata'):
            return LeaseCreateUpdateSerializer

        if self.request.query_params.get('succinct'):
            return LeaseSuccinctSerializer

        if self.action == 'list':
            return LeaseListSerializer

        return LeaseRetrieveSerializer

    def create(self, request, *args, **kwargs):
        if 'preparer' not in request.data:
            request.data['preparer'] = request.user.id

        return super().create(request, *args, **kwargs)

    @action(methods=['get'], detail=True)
    def rent_for_period(self, request, pk=None):
        lease = self.get_object()

        if 'start_date' not in request.query_params or 'end_date' not in request.query_params:
            raise APIException('Both start_date and end_data parameters are mandatory')

        start_date = parser.parse(request.query_params['start_date']).date()
        end_date = parser.parse(request.query_params['end_date']).date()

        result = {
            'start_date': start_date,
            'end_date': end_date,
            'rents': [],
        }

        for rent in lease.rents.all():
            (rent_amount, explanation) = rent.get_amount_for_date_range(start_date, end_date, explain=True)

            explanation_serializer = ExplanationSerializer(explanation)

            result['rents'].append({
                'id': rent.id,
                'start_date': rent.start_date,
                'end_date': rent.end_date,
                'amount': rent_amount,
                'explanation': explanation_serializer.data,
            })

        return Response(result)

    @action(methods=['get'], detail=True)
    def billing_periods(self, request, pk=None):
        lease = self.get_object()

        if 'year' in request.query_params:
            year = int(request.query_params['year'])
        else:
            year = datetime.date.today().year

        start_date = datetime.date(year=year, month=1, day=1)
        end_date = datetime.date(year=year, month=12, day=31)

        billing_periods = []
        for rent in lease.rents.all():
            due_dates_per_year = rent.get_due_dates_for_period(start_date, end_date)
            billing_periods.extend(get_billing_periods_for_year(year, len(due_dates_per_year)))

        return Response({
            'billing_periods': billing_periods
        })

    @action(methods=['post'], detail=True)
    def create_charge(self, request, pk=None):
        lease = self.get_object()
        request.data['lease'] = lease

        serializer = CreateChargeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=201)

    @action(methods=['post'], detail=True)
    def create_collection_letter(self, request, pk=None):
        lease = self.get_object()
        today = datetime.date.today()

        # TODO: remove
        if 'tenant_ids' not in request.data:
            request.data['tenant_ids'] = [request.data['tenant_id']]

        data_keys = {'type', 'collection_charge', 'tenant_ids', 'invoice_ids'}
        if data_keys.difference(set(request.data.keys())):
            raise APIException('All values are mandatory ({})'.format(', '.join(data_keys)))

        type_to_filename = {
            'oikeudenkäyntiuhka': 'oikeudenkayntiuhka.docx',
            'irtisanomis- ja oikeudenkäyntiuhka': 'irtisanomis_ja_oikeudenkayntiuhka.docx',
            'purku-uhka': 'purku_uhka.docx',
        }

        letter_type = request.data.get('type')
        tenants = lease.tenants.filter(id__in=request.data.get('tenant_ids'))
        contacts = []
        for tenant in tenants:
            tenant_contact = tenant.get_billing_tenantcontacts(today, today).first()
            contacts.append(tenant_contact.contact)

        invoice_ids = request.data.get('invoice_ids')
        collection_charge = Decimal(request.data.get('collection_charge'))

        if letter_type not in type_to_filename.keys():
            raise APIException('Unknown type "{}"'.format(letter_type))

        resource_path = Path(apps.get_app_config('leasing').path) / 'resources'
        template_filename = resource_path / type_to_filename[letter_type]

        billing_addresses = ''
        for contact in contacts:
            billing_address = '<w:br/>'.join([
                str(contact),
                contact.address,
                '{} {}'.format(contact.postal_code, contact.city if contact.city else ''),
            ])
            billing_addresses += billing_address + '<w:br/>'

        invoices = lease.invoices.filter(id__in=invoice_ids)
        debt = Decimal(0)
        debt_strings = []
        interest_strings = []
        interest_total = Decimal(0)
        interest_rates = []
        interest_rate_strings = []

        for invoice in invoices:
            penalty_interest_data = invoice.calculate_penalty_interest()
            if not penalty_interest_data['total_interest_amount']:
                continue

            interest_strings.append('Korko laskulle, jonka eräpäivä on ollut {}, on {} euroa'.format(
                invoice.due_date.strftime('%d.%m.%Y'),
                penalty_interest_data['total_interest_amount']
            ))
            interest_total += penalty_interest_data['total_interest_amount']

            invoice_debt_amount = invoice.outstanding_amount
            debt += invoice_debt_amount

            debt_strings.append('{}, {} euroa (ajalta {} - {})'.format(
                invoice.due_date.strftime('%d.%m.%Y'),
                invoice_debt_amount,
                invoice.billing_period_start_date.strftime('%d.%m.%Y'),
                invoice.billing_period_end_date.strftime('%d.%m.%Y')
            ))

            for interest_period in penalty_interest_data['interest_periods']:
                interest_rate_tuple = (interest_period['start_date'], interest_period['end_date'],
                                       interest_period['penalty_rate'])

                if interest_rate_tuple not in interest_rates:
                    interest_rates.append(interest_rate_tuple)

        if len(interest_rates) > 1:
            interest_rates = sorted(interest_rates, key=lambda x: x[0])

            # Squash adjacent equal penalty interest rates
            squashed_interest_rates = []
            for k, g in groupby(interest_rates, key=lambda x: x[2]):
                rate_group = list(g)
                if len(rate_group) == 1:
                    squashed_interest_rates.append(rate_group[0])
                else:
                    squashed_interest_rates.append((rate_group[0][0], rate_group[-1][1], rate_group[0][2]))

            for i, interest_rate in enumerate(squashed_interest_rates):
                if i == len(squashed_interest_rates) - 1:
                    # TODO: Might not be strictly accurate
                    interest_rate_strings.append(
                        'Viivästyskoron suuruus {} alkaen on {} %'.format(interest_rate[0].strftime('%d.%m.%Y'),
                                                                          interest_rate[2]))
                else:
                    interest_rate_strings.append('Viivästyskoron suuruus ajalla {} - {} on {} %'.format(
                        interest_rate[0].strftime('%d.%m.%Y'), interest_rate[1].strftime('%d.%m.%Y'),
                        interest_rate[2]))
        else:
            interest_rate_strings.append('viivästyskoron suuruus on {} %'.format(interest_rates[0][2]))

        collection_charge_total = len(invoices) * collection_charge

        grand_total = debt + interest_total + collection_charge_total

        template_data = {
            'billing_address': billing_addresses,
            'lease_identifier': str(lease.identifier),
            'current_date': today.strftime('%d.%m.%Y'),
            'debts': '<w:br/>'.join(debt_strings),
            'total_debt': debt,
            'interest_rates': '<w:br/>'.join(interest_rate_strings),
            'interests': '<w:br/>'.join(interest_strings),
            'interest_total': interest_total,
            'grand_total': grand_total,
            'collection_charge': collection_charge,
            'collection_charge_total': collection_charge_total,
            'invoice_count': len(invoices),
        }

        doc = DocxTemplate(str(template_filename))
        doc.render(template_data)
        output = io.BytesIO()
        doc.save(output)

        if output.getvalue():
            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

            response['Content-Disposition'] = 'attachment; filename={}_{}'.format(str(lease.identifier),
                                                                                  type_to_filename[letter_type])

            return response
        else:
            raise APIException('Document error')
