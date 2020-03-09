from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.viewsets import ViewSet

from leasing.renderers import BrowsableAPIRendererWithoutForms
from leasing.report.invoice.invoice_payments import InvoicePaymentsReport
from leasing.report.invoice.invoices_in_period import InvoicesInPeriodReport
from leasing.report.invoice.laske_invoice_count_report import LaskeInvoiceCountReport
from leasing.report.invoice.open_invoices_report import OpenInvoicesReport
from leasing.report.lease.invoicing_disabled_report import LeaseInvoicingDisabledReport
from leasing.report.renderers import XLSXRenderer

ENABLED_REPORTS = [
    OpenInvoicesReport,
    InvoicePaymentsReport,
    InvoicesInPeriodReport,
    LaskeInvoiceCountReport,
    LeaseInvoicingDisabledReport,
]


class ReportViewSet(ViewSet):
    permission_classes = (IsAuthenticated, )
    renderer_classes = [
        JSONRenderer,
        BrowsableAPIRendererWithoutForms,
        XLSXRenderer
    ]
    lookup_field = 'report_type'

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
            reports[report_class.slug] = {
                'name': report_class.name,
                'description': report_class.description,
                'url': reverse('report-detail', request=request, kwargs={'report_type': report_class.slug}),
            }

        return Response(reports)

    # The "format" parameter is not used here, but is passed by DRF if using
    # the ".format" suffix.
    def retrieve(self, request, report_type=None, format=None):
        if report_type not in self.report_classes_by_slug.keys():
            raise NotFound(_('Report type not found'))

        self.report = self.report_classes_by_slug[report_type]()

        return self.report.get_response(request)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)

        if isinstance(response, Response) and response.accepted_renderer.format == "xlsx" and self.report:
            response["content-disposition"] = "attachment; filename={}".format(
                self.report.get_filename(response.accepted_renderer.format))

        return response

    def options(self, request, *args, **kwargs):
        metadata_class = self.metadata_class()
        metadata = metadata_class.determine_metadata(request, self)
        metadata['actions'] = {
            'GET': {
            }
        }

        if 'report_type' in kwargs and kwargs['report_type'] in self.report_classes_by_slug:
            report_class = self.report_classes_by_slug[kwargs['report_type']]

            for field_name, field in report_class.input_fields.items():
                metadata['actions']['GET'][field_name] = {
                    "type": field.__class__.__name__,
                    "required": field.required,
                    "read_only": False,
                    "label": field.label,
                }

                if hasattr(field, 'choices'):
                    metadata['actions']['GET'][field_name]["choices"] = [
                        {
                            "value": c[0],
                            "display_name": c[1],
                        } for c in field.choices
                    ]

        return Response(metadata, status=status.HTTP_200_OK)
