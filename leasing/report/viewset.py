from django.forms.models import ModelChoiceIteratorValue
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.viewsets import ViewSet

from leasing.renderers import BrowsableAPIRendererWithoutForms
from leasing.report.invoice.collaterals_report import CollateralsReport
from leasing.report.invoice.invoice_payments import InvoicePaymentsReport
from leasing.report.invoice.invoices_in_period import InvoicesInPeriodReport
from leasing.report.invoice.invoicing_review import InvoicingReviewReport
from leasing.report.invoice.laske_invoice_count_report import LaskeInvoiceCountReport
from leasing.report.invoice.open_invoices_report import OpenInvoicesReport
from leasing.report.invoice.rents_paid_by_contact import RentsPaidByContactReport
from leasing.report.lease.contact_rents import ContactRentsReport
from leasing.report.lease.decision_conditions_report import DecisionConditionsReport
from leasing.report.lease.extra_city_rent import ExtraCityRentReport
from leasing.report.lease.index_types import IndexTypesReport
from leasing.report.lease.invoicing_disabled_report import LeaseInvoicingDisabledReport
from leasing.report.lease.lease_count_report import LeaseCountReport
from leasing.report.lease.lease_statistic_report import LeaseStatisticReport
from leasing.report.lease.lease_statistic_report2 import LeaseStatisticReport2
from leasing.report.lease.rent_adjustments import RentAdjustmentsReport
from leasing.report.lease.rent_compare import RentCompareReport
from leasing.report.lease.rent_forecast import RentForecastReport
from leasing.report.lease.rent_type import RentTypeReport
from leasing.report.lease.reservations import ReservationsReport
from leasing.report.renderers import XLSXRenderer
from leasing.report.report_base import AsyncReportBase

ENABLED_REPORTS = [
    CollateralsReport,
    ContactRentsReport,
    DecisionConditionsReport,
    ExtraCityRentReport,
    IndexTypesReport,
    InvoicePaymentsReport,
    InvoicesInPeriodReport,
    InvoicingReviewReport,
    LaskeInvoiceCountReport,
    LeaseCountReport,
    LeaseInvoicingDisabledReport,
    LeaseStatisticReport,
    LeaseStatisticReport2,
    OpenInvoicesReport,
    RentAdjustmentsReport,
    RentCompareReport,
    RentForecastReport,
    RentTypeReport,
    RentsPaidByContactReport,
    ReservationsReport,
]


class ReportViewSet(ViewSet):
    permission_classes = (IsAuthenticated,)
    renderer_classes = [JSONRenderer, BrowsableAPIRendererWithoutForms, XLSXRenderer]
    lookup_field = "report_type"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.report_classes_by_slug = {}
        for report_class in ENABLED_REPORTS:
            self.report_classes_by_slug[report_class.slug] = report_class

        self.report = None

    # The "format" parameter is not used here, but is passed by DRF if using
    # the ".format" suffix.
    def list(self, request, format=None):
        reports = {}

        for report_class in ENABLED_REPORTS:
            codename = "leasing.can_generate_report_{}".format(report_class.slug)
            if not request.user.has_perm(codename):
                continue

            reports[report_class.slug] = {
                "name": report_class.name,
                "description": report_class.description,
                "url": reverse(
                    "report-detail",
                    request=request,
                    kwargs={"report_type": report_class.slug},
                ),
            }

        reports = dict(sorted(reports.items(), key=lambda x: x[1]["name"]))

        return Response(reports)

    # The "format" parameter is not used here, but is passed by DRF if using
    # the ".format" suffix.
    def retrieve(self, request, report_type=None, format=None):
        if report_type not in self.report_classes_by_slug.keys():
            raise NotFound(_("Report type not found"))

        self.report = self.report_classes_by_slug[report_type]()

        codename = "leasing.can_generate_report_{}".format(report_type)
        if not request.user.has_perm(codename) and not request.user.is_superuser:
            raise PermissionDenied(_("No permission to generate report"))

        return self.report.get_response(request)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)

        if (
            isinstance(response, Response)
            and response.accepted_renderer.format == "xlsx"
            and self.report
        ):
            response["content-disposition"] = "attachment; filename={}".format(
                self.report.get_filename(response.accepted_renderer.format)
            )

        return response

    def options(self, request, *args, **kwargs):
        metadata_class = self.metadata_class()
        metadata = metadata_class.determine_metadata(request, self)
        metadata["actions"] = {"GET": {}}

        if (
            "report_type" in kwargs
            and kwargs["report_type"] in self.report_classes_by_slug
        ):
            report_class = self.report_classes_by_slug[kwargs["report_type"]]
            metadata["name"] = report_class.name
            metadata["description"] = report_class.description

            for field_name, field in report_class.input_fields.items():
                metadata["actions"]["GET"][field_name] = {
                    "type": field.__class__.__name__,
                    "required": field.required,
                    "read_only": False,
                    "label": field.label,
                }

                if hasattr(field, "choices"):
                    choices = []
                    for choice_value, choice_label in field.choices:
                        choices.append(
                            {
                                "value": (
                                    choice_value.value
                                    if isinstance(
                                        choice_value, ModelChoiceIteratorValue
                                    )
                                    else choice_value
                                ),
                                "display_name": choice_label,
                            }
                        )
                    metadata["actions"]["GET"][field_name]["choices"] = choices

            metadata["output_fields"] = report_class.get_output_fields_metadata()
            metadata["is_async"] = issubclass(report_class, AsyncReportBase)
            metadata["is_already_sorted"] = report_class.is_already_sorted

        return Response(metadata, status=status.HTTP_200_OK)
