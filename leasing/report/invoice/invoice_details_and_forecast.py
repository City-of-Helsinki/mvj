from datetime import date
from fractions import Fraction

from dateutil.relativedelta import relativedelta
from django import forms
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from leasing.enums import InvoiceType
from leasing.models import Invoice, ServiceUnit
from leasing.models.invoice import InvoiceRow
from leasing.models.lease import Lease
from leasing.models.vat import Vat
from leasing.report.excel import FormatType
from leasing.report.report_base import AsyncReportBase


class InvoiceDetailsAndForecastReport(AsyncReportBase):
    name = _("Invoice details and forecast")
    description = _(
        "Shows existing invoices for a selected year and forecasts the rest of the year's invoices"
    )
    slug = "invoice_details_and_forecast"
    input_fields = {
        "service_unit": forms.ModelMultipleChoiceField(
            label=_("Service unit"),
            queryset=ServiceUnit.objects.all(),
            required=False,
        ),
        "year": forms.IntegerField(label=_("Year"), required=True),
    }
    output_fields = {
        "invoice_id": {"label": _("Invoice id"), "width": 13},
        "lease_identifier": {"label": _("Lease identifier"), "width": 16},
        "district_id": {"label": _("District id")},
        "district": {"label": _("District"), "width": 16},
        "lease_start_date": {
            "label": _("Lease start date"),
            "format": FormatType.DATE.value,
            "width": 19,
        },
        "lease_end_date": {
            "label": _("Lease end date"),
            "format": FormatType.DATE.value,
            "width": 19,
        },
        "billing_period_start_date": {
            "label": _("Billing period start date"),
            "format": FormatType.DATE.value,
            "width": 19,
        },
        "billing_period_end_date": {
            "label": _("Billing period end date"),
            "format": FormatType.DATE.value,
            "width": 19,
        },
        "notes": {"label": _("Notes"), "width": 40},
        "due_date": {"label": _("Due date"), "format": FormatType.DATE.value},
        "number": {"label": _("Number"), "is_numeric": True},
        "billed_amount": {
            "label": _("Billed amount"),
            "format": FormatType.MONEY.value,
            "width": 13,
        },
        "is_subject_to_vat": {
            "label": _("Subject to VAT"),
            "format": FormatType.BOOLEAN.value,
            "width": 12,
        },
        "billed_amount_including_vat": {
            "label": _("Billed amount including VAT"),
            "format": FormatType.MONEY.value,
            "width": 16,
        },
        "receivable_types": {"label": _("Receivable types"), "width": 25},
        "share_numerator": {"label": _("Share numerator"), "is_numeric": True},
        "share_denominator": {"label": _("Share denominator"), "is_numeric": True},
        "billing_contact": {"label": _("Billing contact"), "width": 30},
        "business_id": {"label": _("Business ID"), "width": 20},
        "intended_uses": {"label": _("Intended uses"), "width": 25},
        "intended_use_note": {"label": _("Intended use note"), "width": 40},
        "sent_to_sap_at": {
            "label": _("Sent to SAP at"),
            "format": FormatType.DATE.value,
            "width": 20,
        },
        "sap_id": {"label": _("SAP ID"), "width": 12},
        "sap_material_codes": {
            "label": _("SAP material codes"),
            "width": 20,
            "is_numeric": True,
        },
        "sap_order_item_numbers": {
            "label": _("SAP order item numbers"),
            "width": 20,
            "is_numeric": True,
        },
        "sap_project_numbers": {"label": _("SAP project numbers"), "width": 20},
        "invoice_type": {"label": _("Invoice type"), "width": 12},
        "rent_types": {"label": _("Rent types"), "width": 20},
        "rent_cycles": {"label": _("Rent cycles"), "width": 20},
    }
    async_task_timeout = 60 * 30

    def get_data(self, input_data):
        service_units = input_data["service_unit"]
        year = input_data["year"]
        invoices = (
            Invoice.objects.select_related(
                "lease__identifier__district",
                "lease__intended_use",
            )
            .prefetch_related(
                "rows__tenant",
                "rows__receivable_type",
                "rows__intended_use",
                "lease__rents",
            )
            .order_by("id")
        )

        if service_units:
            invoices = invoices.filter(service_unit__in=service_units)
        invoices = invoices.filter(due_date__year=year)

        rows = []
        for invoice in invoices:
            rows.append(self._get_row(invoice))

        rows.extend(
            sorted(
                self._get_forecast_rows(year, service_units),
                key=lambda row: (
                    row["billing_period_start_date"] or row["due_date"],
                    row["due_date"],
                ),
            )
        )
        return rows

    def _get_forecast_rows(self, year, service_units):
        forecast_start = max(date(year, 1, 1), timezone.now().date())
        if forecast_start.year > year:
            return

        leases = (
            Lease.objects.filter(invoicing_enabled_at__isnull=False)
            .filter(
                Q(end_date__isnull=True) | Q(end_date__year__gte=year),
                Q(start_date__isnull=True) | Q(start_date__year__lte=year),
            )
            .select_related("identifier__district", "service_unit", "type")
        )
        if service_units:
            leases = leases.filter(service_unit__in=service_units)

        for lease in leases:
            existing_periods = set(
                lease.invoices.filter(
                    generated=True, type=InvoiceType.CHARGE
                ).values_list(
                    "recipient_id",
                    "billing_period_start_date",
                    "billing_period_end_date",
                )
            )
            for month in range(forecast_start.month, 13):
                start_date = max(date(year, month, 1), forecast_start)
                end_date = start_date + relativedelta(day=31)
                period_rents = lease.determine_payable_rents_and_periods(
                    start_date, end_date, dry_run=True
                )
                for invoice_group in lease.calculate_invoices(
                    period_rents, dry_run=True
                ):
                    for invoice in invoice_group:
                        # Key for comparing existing periods to avoid duplicates
                        key = (
                            invoice["recipient"].pk,
                            invoice["billing_period_start_date"],
                            invoice["billing_period_end_date"],
                        )
                        if key in existing_periods:
                            continue

                        invoice_rows = []
                        for row_data in invoice["rows"]:
                            invoice_rows.append(InvoiceRow(**row_data))
                        invoice_data = invoice.copy()
                        invoice_data.pop("rows")
                        invoice_data.pop("explanations")
                        invoice_data.pop("calculation_result")
                        invoice = Invoice(**invoice_data)

                        yield self._get_row(invoice, invoice_rows=invoice_rows)

    def _get_row(self, invoice: Invoice, invoice_rows=None):
        lease: Lease = invoice.lease
        if invoice_rows is None:
            invoice_rows = invoice.rows.all()
        tenants = {row.tenant for row in invoice_rows if row.tenant is not None}
        share = sum(
            (
                Fraction(tenant.share_numerator, tenant.share_denominator)
                for tenant in tenants
            ),
            Fraction(),
        )

        return {
            "invoice_id": invoice.id,
            "lease_identifier": lease.identifier.identifier,
            "district_id": lease.identifier.district_id,
            "district": lease.identifier.district.name,
            "lease_start_date": lease.start_date,
            "lease_end_date": lease.end_date,
            "billing_period_start_date": invoice.billing_period_start_date,
            "billing_period_end_date": invoice.billing_period_end_date,
            "notes": invoice.notes,
            "due_date": invoice.due_date,
            "number": invoice.number,
            "billed_amount": invoice.billed_amount,
            "is_subject_to_vat": lease.is_subject_to_vat,
            "billed_amount_including_vat": self.get_billed_amount_including_vat(
                lease, invoice
            ),
            "receivable_types": self._get_related_names(
                invoice_rows, "receivable_type"
            ),
            "share_numerator": share.numerator if tenants else None,
            "share_denominator": share.denominator if tenants else None,
            "billing_contact": (
                invoice.recipient.get_name()
                if invoice.recipient.business_id
                else "YKSITYINEN"
            ),
            "business_id": (
                invoice.recipient.business_id if invoice.recipient.business_id else None
            ),
            "intended_uses": self._get_related_names(invoice_rows, "intended_use"),
            "intended_use_note": lease.intended_use_note,
            "sent_to_sap_at": (
                timezone.localtime(invoice.sent_to_sap_at).replace(tzinfo=None)
                if invoice.sent_to_sap_at
                else None
            ),
            "sap_id": invoice.sap_id,
            "sap_material_codes": self._get_related_attribute_values(
                invoice_rows, "receivable_type", "sap_material_code"
            ),
            "sap_order_item_numbers": self._get_related_attribute_values(
                invoice_rows, "receivable_type", "sap_order_item_number"
            ),
            "sap_project_numbers": self._get_related_attribute_values(
                invoice_rows, "receivable_type", "sap_project_number"
            ),
            "invoice_type": str(invoice.type),
            "rent_types": self._get_attribute_values(lease.rents.all(), "type"),
            "rent_cycles": self._get_attribute_values(lease.rents.all(), "cycle"),
        }

    @staticmethod
    def get_billed_amount_including_vat(lease: Lease, invoice: Invoice):
        if lease.is_subject_to_vat:
            vat: Vat = Vat.objects.get_for_date(
                invoice.billing_period_end_date or invoice.invoicing_date
            )
            return invoice.billed_amount * (1 + vat.percent / 100)
        return invoice.billed_amount

    @staticmethod
    def _get_related_names(rows, attribute):
        return ", ".join(
            sorted({str(value) for row in rows if (value := getattr(row, attribute))})
        )

    @staticmethod
    def _get_attribute_values(objects, attribute):
        return ", ".join(
            sorted(
                {
                    str(value)
                    for obj in objects
                    if (value := getattr(obj, attribute)) is not None
                }
            )
        )

    @staticmethod
    def _get_related_attribute_values(rows, related_attribute, attribute):
        return ", ".join(
            sorted(
                {
                    str(value)
                    for row in rows
                    if (related_object := getattr(row, related_attribute))
                    and (value := getattr(related_object, attribute)) is not None
                }
            )
        )
