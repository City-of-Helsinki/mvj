import datetime
import os
from decimal import Decimal
from itertools import groupby

from dateutil import parser
from dateutil.relativedelta import relativedelta
from dateutil.rrule import MONTHLY, rrule
from django.db.models import DurationField, Q
from django.db.models.functions import Cast
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from leasing.filters import DistrictFilter, LeaseFilter
from leasing.forms import LeaseSearchForm
from leasing.models import (
    District, Financing, Hitas, IntendedUse, Lease, LeaseType, Management, Municipality, NoticePeriod, PlanUnit, Plot,
    Regulation, RelatedLease, StatisticalUse, SupportiveHousing)
from leasing.models.utils import get_billing_periods_for_year
from leasing.serializers.debt_collection import CreateCollectionLetterDocumentSerializer
from leasing.serializers.explanation import ExplanationSerializer
from leasing.serializers.invoice import CreateChargeSerializer, InvoiceSerializerWithExplanations
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


def interest_rates_to_strings(interest_rates):
    result = []
    sorted_interest_rates = sorted(interest_rates, key=lambda x: x[0])

    if len(sorted_interest_rates) == 1:
        return [_('the penalty interest rate is {interest_percent} %').format(
            interest_percent=sorted_interest_rates[0][2])]

    # Squash adjacent equal penalty interest rates
    squashed_interest_rates = []
    for k, g in groupby(sorted_interest_rates, key=lambda x: x[2]):
        rate_group = list(g)
        if len(rate_group) == 1:
            squashed_interest_rates.append(rate_group[0])
        else:
            squashed_interest_rates.append((rate_group[0][0], rate_group[-1][1], rate_group[0][2]))

    for i, interest_rate in enumerate(squashed_interest_rates):
        if i == len(squashed_interest_rates) - 1:
            # TODO: Might not be strictly accurate
            result.append(
                _('The penalty interest rate starting on {start_date} is {interest_percent} %').format(
                    start_date=interest_rate[0].strftime('%d.%m.%Y'), interest_percent=interest_rate[2]))
        else:
            result.append(
                _('The penalty interest rate between {start_date} and {end_date} is {interest_percent} %').format(
                    start_date=interest_rate[0].strftime('%d.%m.%Y'),
                    end_date=interest_rate[1].strftime('%d.%m.%Y'), interest_percent=interest_rate[2]))

    return result


class LeaseViewSet(AuditLogMixin, AtomicTransactionModelViewSet):
    serializer_class = LeaseRetrieveSerializer
    filterset_class = LeaseFilter

    def get_queryset(self):  # noqa: C901
        """Allow filtering leases by various query parameters

        `identifier` query parameter can be used to find the Lease with the provided identifier.
        example: .../lease/?identifier=S0120-219
        """
        identifier = self.request.query_params.get('identifier')
        succinct = self.request.query_params.get('succinct')

        if succinct:
            queryset = Lease.objects.succinct_select_related_and_prefetch_related()
        else:
            queryset = Lease.objects.full_select_related_and_prefetch_related()

        if self.action != 'list':
            return queryset

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

        search_form = LeaseSearchForm(self.request.query_params)

        if search_form.is_valid():
            if search_form.cleaned_data.get('tenant'):
                queryset = queryset.filter(
                    Q(tenants__tenantcontact__contact__name__icontains=search_form.cleaned_data.get('tenant')) |
                    Q(tenants__tenantcontact__contact__first_name__icontains=search_form.cleaned_data.get('tenant')) |
                    Q(tenants__tenantcontact__contact__last_name__icontains=search_form.cleaned_data.get('tenant'))
                )

                # Limit further only if searching by tenants
                if search_form.cleaned_data.get('tenant_role'):
                    tenant_roles = [r.strip() for r in search_form.cleaned_data.get('tenant_role').split(',')]
                    queryset = queryset.filter(tenants__tenantcontact__type__in=tenant_roles)

                if search_form.cleaned_data.get('only_past_tentants'):
                    queryset = queryset.filter(tenants__tenantcontact__end_date__lte=datetime.date.today())

            if search_form.cleaned_data.get('sequence'):
                queryset = queryset.filter(identifier__sequence=search_form.cleaned_data.get('sequence'))

            if search_form.cleaned_data.get('lease_start_date_start'):
                queryset = queryset.filter(start_date__gte=search_form.cleaned_data.get('lease_start_date_start'))

            if search_form.cleaned_data.get('lease_start_date_end'):
                queryset = queryset.filter(start_date__lte=search_form.cleaned_data.get('lease_start_date_end'))

            if search_form.cleaned_data.get('lease_end_date_start'):
                queryset = queryset.filter(end_date__gte=search_form.cleaned_data.get('lease_end_date_start'))

            if search_form.cleaned_data.get('lease_end_date_end'):
                queryset = queryset.filter(end_date__lte=search_form.cleaned_data.get('lease_end_date_end'))

            if search_form.cleaned_data.get('ongoing'):
                queryset = queryset.filter(
                    (Q(start_date__isnull=True) | Q(start_date__lte=datetime.date.today())) &
                    (Q(end_date__isnull=True) | Q(end_date__gte=datetime.date.today()))
                )

            if search_form.cleaned_data.get('expired'):
                queryset = queryset.filter(end_date__lte=datetime.date.today())

            if search_form.cleaned_data.get('property_identifier'):
                queryset = queryset.filter(
                    lease_areas__identifier__icontains=search_form.cleaned_data.get('property_identifier'))

            if search_form.cleaned_data.get('address'):
                queryset = queryset.filter(
                    lease_areas__addresses__address__icontains=search_form.cleaned_data.get('address'))

            if search_form.cleaned_data.get('state'):
                states = [s.strip() for s in search_form.cleaned_data.get('state').split(',')]
                queryset = queryset.filter(state__in=states)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update', 'metadata'):
            # TODO: Kludge
            # Can be replaced with a custom function when DRF 3.9 is released. e.g.
            #
            #    @create_charge.mapping.options
            #    def create_charge_options(self, request, *args, **kwargs):
            #         data = CreateChargeSerializer().determine_metadata(request, self)
            #         return Response(data, status=status.HTTP_200_OK)
            #
            # See: http://www.django-rest-framework.org/api-guide/viewsets/#routing-additional-http-methods-for-extra-actions  # noqa
            if self.action == 'metadata':
                if self.request._request.resolver_match.view_name == 'lease-create-charge':
                    return CreateChargeSerializer

                if self.request._request.resolver_match.view_name == 'lease-create-collection-letter':
                    return CreateCollectionLetterDocumentSerializer

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

        try:
            start_date = parser.parse(request.query_params['start_date']).date()
            end_date = parser.parse(request.query_params['end_date']).date()
        except ValueError:
            raise APIException(_('Start date or end date is invalid'))

        if start_date > end_date:
            raise APIException(_('Start date cannot be after end date'))

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
            try:
                year = int(request.query_params['year'])
            except ValueError:
                raise APIException(_('Year parameter is not valid'))
        else:
            year = datetime.date.today().year

        try:
            start_date = datetime.date(year=year, month=1, day=1)
            end_date = datetime.date(year=year, month=12, day=31)
        except ValueError as e:
            raise APIException(e)

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

        request.data['lease'] = lease
        serializer = CreateCollectionLetterDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        collection_charge = Decimal(serializer.validated_data['collection_charge'])
        invoices = serializer.validated_data['invoices']
        debt = Decimal(0)
        debt_strings = []
        interest_strings = []
        interest_total = Decimal(0)
        interest_rates = set()
        billing_addresses = []

        for tenant in serializer.validated_data['tenants']:
            billing_tenantcontact = tenant.get_billing_tenantcontacts(today, today).first()

            if not billing_tenantcontact or not billing_tenantcontact.contact:
                raise APIException(_('No billing info or billing info does not have a contact address'))

            billing_addresses.append('<w:br/>'.join([
                str(billing_tenantcontact.contact), billing_tenantcontact.contact.address,
                '{} {}'.format(billing_tenantcontact.contact.postal_code,
                               billing_tenantcontact.contact.city if billing_tenantcontact.contact.city else '')
            ]))

        for invoice in invoices:
            penalty_interest_data = invoice.calculate_penalty_interest()
            if not penalty_interest_data['total_interest_amount']:
                continue

            interest_strings.append(
                _('Penalty interest for the invoice with the due date of {due_date} is {interest_amount} euroa').format(
                    due_date=invoice.due_date.strftime('%d.%m.%Y'),
                    interest_amount=penalty_interest_data['total_interest_amount']
                ))
            interest_total += penalty_interest_data['total_interest_amount']

            invoice_debt_amount = invoice.outstanding_amount
            debt += invoice_debt_amount

            debt_strings.append(_('{due_date}, {debt_amount} euro (between {start_date} and {end_date})').format(
                due_date=invoice.due_date.strftime('%d.%m.%Y'),
                debt_amount=invoice_debt_amount,
                start_date=invoice.billing_period_start_date.strftime('%d.%m.%Y'),
                end_date=invoice.billing_period_end_date.strftime('%d.%m.%Y')
            ))

            for interest_period in penalty_interest_data['interest_periods']:
                interest_rate_tuple = (interest_period['start_date'], interest_period['end_date'],
                                       interest_period['penalty_rate'])

                interest_rates.add(interest_rate_tuple)

        collection_charge_total = len(invoices) * collection_charge
        grand_total = debt + interest_total + collection_charge_total

        template_data = {
            'lease_details': '<w:br/>'.join(lease.get_lease_info_text(tenants=serializer.validated_data['tenants'])),
            'billing_address': '<w:br/><w:br/>'.join(billing_addresses),
            'lease_identifier': str(lease.identifier),
            'current_date': today.strftime('%d.%m.%Y'),
            'debts': '<w:br/>'.join(debt_strings),
            'total_debt': debt,
            'interest_rates': '<w:br/>'.join(interest_rates_to_strings(interest_rates)),
            'interests': '<w:br/>'.join(interest_strings),
            'interest_total': interest_total,
            'grand_total': grand_total,
            'collection_charge': collection_charge,
            'collection_charge_total': collection_charge_total,
            'invoice_count': len(invoices),
        }

        doc = serializer.validated_data['template'].render_document(template_data)

        if not doc:
            raise APIException(_('Error creating the document from the template'))

        response = HttpResponse(
            doc, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

        response['Content-Disposition'] = 'attachment; filename={}_{}'.format(
            str(lease.identifier), os.path.basename(serializer.validated_data['template'].file.name))

        return response

    @action(methods=['get'], detail=True)
    def preview_invoices_for_year(self, request, pk=None):
        lease = self.get_object()

        if 'year' in request.query_params:
            try:
                year = int(request.query_params['year'])
            except ValueError:
                raise APIException(_('Year parameter is not valid'))
        else:
            year = datetime.date.today().year

        try:
            first_day_of_year = datetime.date(year=year, month=1, day=1)
        except ValueError as e:
            raise APIException(e)

        first_day_of_every_month = [dt.date() for dt in rrule(freq=MONTHLY, count=12, dtstart=first_day_of_year)]

        result = []

        for first_day in first_day_of_every_month:
            last_day = first_day + relativedelta(day=31)

            rents = lease.determine_payable_rents_and_periods(first_day, last_day)

            for period_invoice_data in lease.calculate_invoices(rents):
                period_invoices = []
                for invoice_data in period_invoice_data:
                    invoice_serializer = InvoiceSerializerWithExplanations(invoice_data)
                    period_invoices.append(invoice_serializer.data)

                result.append(period_invoices)

        return Response(result)

    @action(methods=['post'], detail=True)
    def copy_areas_to_contract(self, request, pk=None):
        lease = self.get_object()

        item_types = [
            {
                'class': Plot,
                'manager_name': 'plots',
            },
            {
                'class': PlanUnit,
                'manager_name': 'plan_units',
            }
        ]

        for lease_area in lease.lease_areas.all():
            for item_type in item_types:
                for item in getattr(lease_area, item_type['manager_name']).filter(in_contract=False):
                    match_data = {
                        'lease_area': lease_area,
                        'identifier': item.identifier,
                        'in_contract': True,
                    }

                    defaults = {}
                    for field in item_type['class']._meta.get_fields():
                        if field.name in ['id', 'lease_area', 'created_at', 'modified_at', 'in_contract']:
                            continue
                        defaults[field.name] = getattr(item, field.name)

                    (new_item, new_item_created) = item_type['class'].objects.update_or_create(
                        defaults=defaults, **match_data)

        return Response({'success': True})

    @action(methods=['post'], detail=True)
    def set_invoicing_state(self, request, pk=None):
        lease = self.get_object()

        if 'invoicing_enabled' not in request.data:
            raise APIException('"invoicing_enabled" key is required')

        if request.data['invoicing_enabled'] is not True and request.data['invoicing_enabled'] is not False:
            raise APIException('"invoicing_enabled" value has to be true or false')

        lease.set_is_invoicing_enabled(request.data['invoicing_enabled'])

        return Response({'success': True})

    @action(methods=['post'], detail=True)
    def set_rent_info_completion_state(self, request, pk=None):
        lease = self.get_object()

        if 'rent_info_complete' not in request.data:
            raise APIException('"rent_info_complete" key is required')

        if request.data['rent_info_complete'] is not True and request.data['rent_info_complete'] is not False:
            raise APIException('"rent_info_complete" value has to be true or false')

        lease.set_is_rent_info_complete(request.data['rent_info_complete'])

        return Response({'success': True})
