import datetime
import logging
import os
import sys
from decimal import Decimal
from itertools import groupby

from dateutil import parser
from dateutil.relativedelta import relativedelta
from dateutil.rrule import MONTHLY, rrule
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from rest_framework import status, viewsets
from rest_framework.exceptions import APIException
from rest_framework.exceptions import ValidationError as DrfValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from leasing.models import Lease, PlanUnit, Plot
from leasing.models.utils import get_billing_periods_for_year
from leasing.permissions import PerMethodPermission
from leasing.serializers.debt_collection import CreateCollectionLetterDocumentSerializer
from leasing.serializers.explanation import ExplanationSerializer
from leasing.serializers.invoice import (
    CreateChargeSerializer,
    InvoiceSerializerWithExplanations,
)
from leasing.viewsets.utils import AtomicTransactionMixin

logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(stdout_handler)
logger.setLevel(logging.INFO)


class LeaseCreateChargeViewSet(AtomicTransactionMixin, viewsets.GenericViewSet):
    serializer_class = CreateChargeSerializer
    permission_classes = (PerMethodPermission,)
    perms_map = {"POST": ["leasing.add_invoice"]}

    def get_view_name(self):
        return _("Create charge")

    def get_view_description(self, html=False):
        return _("Create charge shared to tenants by their shares")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


def interest_rates_to_strings(interest_rates):
    result = []
    sorted_interest_rates = sorted(interest_rates, key=lambda x: x[0])

    if len(sorted_interest_rates) == 1:
        return [
            _("the penalty interest rate is {interest_percent} %").format(
                interest_percent=sorted_interest_rates[0][2]
            )
        ]

    # Squash adjacent equal penalty interest rates
    squashed_interest_rates = []
    for k, g in groupby(sorted_interest_rates, key=lambda x: x[2]):
        rate_group = list(g)
        if len(rate_group) == 1:
            squashed_interest_rates.append(rate_group[0])
        else:
            squashed_interest_rates.append(
                (rate_group[0][0], rate_group[-1][1], rate_group[0][2])
            )

    for i, interest_rate in enumerate(squashed_interest_rates):
        if i == len(squashed_interest_rates) - 1:
            # TODO: Might not be strictly accurate
            result.append(
                _(
                    "The penalty interest rate starting on {start_date} is {interest_percent} %"
                ).format(
                    start_date=interest_rate[0].strftime("%d.%m.%Y"),
                    interest_percent=interest_rate[2],
                )
            )
        else:
            result.append(
                _(
                    "The penalty interest rate between {start_date} and {end_date} is {interest_percent} %"
                ).format(
                    start_date=interest_rate[0].strftime("%d.%m.%Y"),
                    end_date=interest_rate[1].strftime("%d.%m.%Y"),
                    interest_percent=interest_rate[2],
                )
            )

    return result


class LeaseCreateCollectionLetterDocumentViewSet(
    AtomicTransactionMixin, viewsets.GenericViewSet
):
    serializer_class = CreateCollectionLetterDocumentSerializer
    permission_classes = (PerMethodPermission,)
    perms_map = {"POST": ["leasing.add_collectionletter"]}

    def get_view_name(self):
        return _("Create collection letter document")

    def create(self, request, *args, **kwargs):
        today = datetime.date.today()

        serializer = CreateCollectionLetterDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invoices = serializer.validated_data["invoices"]
        debt = Decimal(0)
        debt_strings = []
        interest_strings = []
        interest_total = Decimal(0)
        interest_rates = set()
        billing_addresses = []

        for tenant in serializer.validated_data["tenants"]:
            billing_tenantcontact = tenant.get_billing_tenantcontacts(
                today, today
            ).first()

            if not billing_tenantcontact or not billing_tenantcontact.contact:
                raise APIException(
                    _("No billing info or billing info does not have a contact address")
                )

            billing_addresses.append(
                "<w:br/>".join(
                    [
                        str(billing_tenantcontact.contact),
                        (
                            billing_tenantcontact.contact.address
                            if billing_tenantcontact.contact.address
                            else ""
                        ),
                        "{} {}".format(
                            (
                                billing_tenantcontact.contact.postal_code
                                if billing_tenantcontact.contact.postal_code
                                else ""
                            ),
                            (
                                billing_tenantcontact.contact.city
                                if billing_tenantcontact.contact.city
                                else ""
                            ),
                        ),
                    ]
                )
            )

        collection_charge_total = Decimal(0)

        for invoice_datum in invoices:
            invoice = invoice_datum["invoice"]
            penalty_interest_data = invoice.calculate_penalty_interest()

            if penalty_interest_data["total_interest_amount"]:
                interest_strings.append(
                    _(
                        "Penalty interest for the invoice with the due date of {due_date} is {interest_amount} euroa"
                    ).format(
                        due_date=invoice.due_date.strftime("%d.%m.%Y"),
                        interest_amount=penalty_interest_data["total_interest_amount"],
                    )
                )
                interest_total += penalty_interest_data["total_interest_amount"]

            invoice_debt_amount = invoice.outstanding_amount
            debt += invoice_debt_amount

            debt_strings.append(
                _(
                    "{due_date}, {debt_amount} euro (between {start_date} and {end_date})"
                ).format(
                    due_date=invoice.due_date.strftime("%d.%m.%Y"),
                    debt_amount=invoice_debt_amount,
                    start_date=invoice.billing_period_start_date.strftime("%d.%m.%Y"),
                    end_date=invoice.billing_period_end_date.strftime("%d.%m.%Y"),
                )
            )

            for interest_period in penalty_interest_data["interest_periods"]:
                interest_rate_tuple = (
                    interest_period["start_date"],
                    interest_period["end_date"],
                    interest_period["penalty_rate"],
                )

                interest_rates.add(interest_rate_tuple)

            collection_charge_total += Decimal(invoice_datum["collection_charge"])

        grand_total = debt + interest_total + collection_charge_total

        lease = serializer.validated_data["lease"]

        template_data = {
            "lease_details": "<w:br/>".join(
                lease.get_lease_info_text(tenants=serializer.validated_data["tenants"])
            ),
            "billing_address": "<w:br/><w:br/>".join(billing_addresses),
            "lease_identifier": str(lease.identifier),
            "current_date": today.strftime("%d.%m.%Y"),
            "debts": "<w:br/>".join(debt_strings),
            "total_debt": debt,
            "interest_rates": "<w:br/>".join(interest_rates_to_strings(interest_rates)),
            "interests": "<w:br/>".join(interest_strings),
            "interest_total": interest_total,
            "grand_total": grand_total,
            "collection_charge_total": collection_charge_total,
            "invoice_count": len(invoices),
        }

        doc = serializer.validated_data["template"].render_document(template_data)

        if not doc:
            raise DrfValidationError(_("Error creating the document from the template"))

        response = HttpResponse(
            doc,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        response["Content-Disposition"] = "attachment; filename={}_{}".format(
            str(lease.identifier),
            os.path.basename(
                serializer.validated_data["template"].file.name.replace("_template", "")
            ),
        )

        return response


def get_lease_from_query_params(query_params):
    if not query_params.get("lease"):
        raise APIException("lease parameter is mandatory")

    try:
        return Lease.objects.get(pk=int(query_params.get("lease")))
    except Lease.DoesNotExist:
        raise APIException("Lease does not exist")
    except ValueError:
        raise APIException("Invalid lease id")


class LeaseRentForPeriodView(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"GET": ["leasing.view_invoice"]}

    def get_view_name(self):
        return _("Rent for period")

    def get_view_description(self, html=False):
        return _("View rent amounts for a given period")

    def get(self, request, format=None):
        lease = get_lease_from_query_params(request.query_params)

        if (
            "start_date" not in request.query_params
            or "end_date" not in request.query_params
        ):
            raise APIException("Both start_date and end_data parameters are mandatory")

        try:
            start_date = parser.parse(request.query_params["start_date"]).date()
            end_date = parser.parse(request.query_params["end_date"]).date()
        except ValueError:
            raise APIException(_("Start date or end date is invalid"))

        if start_date > end_date:
            raise APIException(_("Start date cannot be after end date"))

        result = {"start_date": start_date, "end_date": end_date, "rents": []}

        for rent in lease.rents.all():
            if not rent.is_active_in_period(start_date, end_date):
                continue

            calculation_result = rent.get_amount_for_date_range(
                start_date, end_date, dry_run=True
            )

            explanation_serializer = ExplanationSerializer(
                calculation_result.get_explanation()
            )

            result["rents"].append(
                {
                    "id": rent.id,
                    "start_date": rent.start_date,
                    "end_date": rent.end_date,
                    "amount": calculation_result.get_total_amount(),
                    "explanation": explanation_serializer.data,
                }
            )

        return Response(result)


class LeaseBillingPeriodsView(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"GET": ["leasing.view_invoice"]}

    def get_view_name(self):
        return _("List billing periods for year")

    def get(self, request, format=None):
        lease = get_lease_from_query_params(request.query_params)

        if "year" in request.query_params:
            try:
                year = int(request.query_params["year"])
            except (ValueError, OverflowError):
                raise APIException(_("Year parameter is not valid"))
        else:
            year = datetime.date.today().year

        try:
            start_date = datetime.date(year=year, month=1, day=1)
            end_date = datetime.date(year=year, month=12, day=31)
        except (ValueError, OverflowError) as e:
            raise APIException(e)

        billing_periods = []
        for rent in lease.rents.all():
            due_dates_for_year = rent.get_due_dates_for_period(start_date, end_date)
            billing_periods.extend(
                get_billing_periods_for_year(year, len(due_dates_for_year))
            )

        return Response({"billing_periods": billing_periods})


class LeasePreviewInvoicesForYearView(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"GET": ["leasing.view_invoice"]}

    def get_view_name(self):
        return _("Preview invoices for year")

    def get(self, request, format=None):
        lease = get_lease_from_query_params(request.query_params)

        if "year" in request.query_params:
            try:
                year = int(request.query_params["year"])
            except (ValueError, OverflowError):
                raise APIException(_("Year parameter is not valid"))
        else:
            year = datetime.date.today().year

        try:
            first_day_of_year = datetime.date(year=year, month=1, day=1)
        except (ValueError, OverflowError) as e:
            raise APIException(e)

        first_day_of_every_month = [
            dt.date() for dt in rrule(freq=MONTHLY, count=12, dtstart=first_day_of_year)
        ]

        result = []

        for first_day in first_day_of_every_month:
            last_day = first_day + relativedelta(day=31)

            rents = lease.determine_payable_rents_and_periods(
                first_day, last_day, dry_run=True
            )

            for period_invoice_data in lease.calculate_invoices(rents, dry_run=True):
                period_invoices = []
                for invoice_data in period_invoice_data:
                    invoice_serializer = InvoiceSerializerWithExplanations(invoice_data)
                    period_invoices.append(invoice_serializer.data)

                result.append(period_invoices)

        return Response(result)


class LeaseCopyAreasToContractView(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"POST": ["leasing.add_leasearea"]}

    def get_view_name(self):
        return _("Copy areas to contract")

    def get_view_description(self, html=False):
        return _('Duplicates current areas and marks them "in contract"')

    def post(self, request, format=None):
        lease = get_lease_from_query_params(request.query_params)

        item_types = [
            {"class": Plot, "manager_name": "plots"},
            {"class": PlanUnit, "manager_name": "plan_units"},
        ]

        for lease_area in lease.lease_areas.all():
            for item_type in item_types:
                for item in getattr(lease_area, item_type["manager_name"]).filter(
                    in_contract=False, is_master=True
                ):
                    match_data = {
                        "lease_area": lease_area,
                        "identifier": item.identifier,
                        "in_contract": True,
                    }

                    defaults = {}
                    for field in item_type["class"]._meta.get_fields():
                        if field.name in [
                            "id",
                            "lease_area",
                            "created_at",
                            "modified_at",
                            "in_contract",
                            "is_master",
                            "plotsearch",
                            "plotsearchtarget",
                            "usage_distributions",
                        ]:
                            continue
                        defaults[field.name] = getattr(item, field.name)

                    (new_item, new_item_created) = item_type[
                        "class"
                    ].objects.update_or_create(defaults=defaults, **match_data)

        return Response({"success": True})


class LeaseSetInvoicingStateView(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"POST": ["leasing.change_lease_invoicing_enabled_at"]}

    def get_view_name(self):
        return _("Set invoicing state")

    def get_view_description(self):
        return _("Sets invoicing state for lease to true or false")

    def post(self, request, format=None):
        lease = get_lease_from_query_params(request.query_params)

        if "invoicing_enabled" not in request.data:
            raise APIException('"invoicing_enabled" key is required')

        invoicing_enabled_new_status = request.data["invoicing_enabled"]
        if (
            invoicing_enabled_new_status is not True
            and invoicing_enabled_new_status is not False
        ):
            raise APIException('"invoicing_enabled" value has to be true or false')

        if invoicing_enabled_new_status and lease.rent_info_completed_at is None:
            raise APIException(
                _("Cannot enable invoicing if rent info is not completed")
            )

        try:
            lease.set_invoicing_enabled(invoicing_enabled_new_status)
        except DjangoValidationError as e:
            if invoicing_enabled_new_status is True:
                # We don't want to raise validation errors when disabling invoicing,
                # only when trying to enable it.
                raise DrfValidationError(str(e.args))
        except Exception as e:
            logger.error(
                f"Error setting invoicing state for lease {lease.pk}: {str(e)}"
            )
            raise APIException(_("Failed to set invoicing state: {}").format(str(e)))

        return Response(
            {"success": True, "invoicing_enabled_at": lease.invoicing_enabled_at}
        )


class LeaseSetRentInfoCompletionStateView(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"POST": ["leasing.change_lease_rent_info_completed_at"]}

    def get_view_name(self):
        return _("Set rent info completion state")

    def post(self, request, format=None):
        lease = get_lease_from_query_params(request.query_params)

        if "rent_info_complete" not in request.data:
            raise APIException('"rent_info_complete" key is required')

        rent_info_new_status = request.data["rent_info_complete"]
        if rent_info_new_status is not True and rent_info_new_status is not False:
            raise APIException('"rent_info_complete" value has to be true or false')

        if rent_info_new_status is True:
            # We don't want to validate when setting the completion to false,
            # only when trying to set it to true.
            try:
                lease.validate_rents()
            except DjangoValidationError as e:
                raise DrfValidationError(
                    _("Cannot complete rent info: {}").format(str(e.args))
                )

        lease.set_rent_info_complete(rent_info_new_status)

        return Response(
            {"success": True, "rent_info_completed_at": lease.rent_info_completed_at}
        )
