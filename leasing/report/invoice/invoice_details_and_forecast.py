from decimal import Decimal

from django import forms
from django.db.models import Prefetch
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from leasing.enums import TenantContactType
from leasing.models import Invoice, ServiceUnit, TenantContact
from leasing.models.contact import Contact
from leasing.models.lease import Lease
from leasing.models.tenant import Tenant
from leasing.report.excel import FormatType
from leasing.report.report_base import AsyncReportBase

# TODO improve: will possibly change at some point in the future
# and no one reading this report will know that it hasn't been updated.
VAT_MULTIPLIER = Decimal("1.225")


class InvoiceDetailsAndForecastReport(AsyncReportBase):
    name = _("Invoice details and forecast")
    description = _("Shows invoice details and forecast of future invoices")
    slug = "invoice_details_and_forecast"
    input_fields = {
        "service_unit": forms.ModelMultipleChoiceField(
            label=_("Service unit"),
            queryset=ServiceUnit.objects.all(),
            required=False,
        ),
        # TODO: add support for multiple years?
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
        "total_amount": {
            "label": _("Total amount"),
            "format": FormatType.MONEY.value,
            "width": 13,
        },
        "is_subject_to_vat": {
            "label": _("Subject to VAT"),
            "format": FormatType.BOOLEAN.value,
            "width": 12,
        },
        "total_amount_including_vat": {
            "label": _("Total amount including VAT"),
            "format": FormatType.MONEY.value,
            "width": 16,
        },
        "receivable_types": {"label": _("Receivable types"), "width": 25},
        "tenant": {"label": _("Tenant"), "width": 30},
        "share_numerator": {"label": _("Share numerator"), "is_numeric": True},
        "share_denominator": {"label": _("Share denominator"), "is_numeric": True},
        "billing_contact": {"label": _("Billing contact"), "width": 30},
        "intended_uses": {"label": _("Intended uses"), "width": 25},
        "intended_use_note": {"label": _("Intended use note"), "width": 40},
        "sent_to_sap_at": {
            "label": _("Sent to SAP at"),
            "format": FormatType.DATE.value,
            "width": 20,
        },
        "invoice_type": {"label": _("Invoice type"), "width": 12},
        "rent_types": {"label": _("Rent types"), "width": 20},
        "rent_cycles": {"label": _("Rent cycles"), "width": 20},
    }
    async_task_timeout = 60 * 30

    def get_data(self, input_data):
        current_contacts = TenantContact.objects.filter(
            end_date__isnull=True
        ).select_related("contact")
        invoices = (
            Invoice.objects.select_related(
                "lease__identifier__district",
                "lease__intended_use",
            )
            .prefetch_related(
                "rows__receivable_type",
                "rows__intended_use",
                "lease__rents",
                "lease__tenants",
                Prefetch(
                    "lease__tenants__tenantcontact_set", queryset=current_contacts
                ),
            )
            .order_by("id")
        )

        if input_data["service_unit"]:
            invoices = invoices.filter(
                rows__service_unit__in=input_data["service_unit"]
            )
        if input_data["start_date"]:
            invoices = invoices.filter(due_date__gte=input_data["start_date"])
        if input_data["end_date"]:
            invoices = invoices.filter(due_date__lte=input_data["end_date"])
        if input_data["year"]:
            invoices = invoices.filter(due_date__year=input_data["year"])

        rows = []
        for invoice in invoices:
            lease = invoice.lease
            tenants = lease.tenants.all()
            for tenant in tenants:
                rows.append(self._get_row(invoice, tenant))

        return rows

    def _get_row(self, invoice: Invoice, tenant: Tenant):
        lease: Lease = invoice.lease
        current_contacts = tenant.tenantcontact_set.all() if tenant else []
        tenant_names = self._get_contact_names(
            current_contacts, TenantContactType.TENANT
        )
        billing_names = self._get_contact_names(
            current_contacts, TenantContactType.BILLING
        )

        return {
            "invoice_id": invoice.id,
            "lease_identifier": lease.identifier.identifier,
            "district_id": lease.identifier.district_id,  # Should be district? Currently just a DB ID.
            "district": lease.identifier.district.name,
            "lease_start_date": lease.start_date,
            "lease_end_date": lease.end_date,
            "billing_period_start_date": invoice.billing_period_start_date,
            "billing_period_end_date": invoice.billing_period_end_date,
            "notes": invoice.notes,
            "due_date": invoice.due_date,
            "number": invoice.number,
            "total_amount": invoice.total_amount,
            "is_subject_to_vat": lease.is_subject_to_vat,
            "total_amount_including_vat": self.get_total_amount_including_vat(
                lease, invoice
            ),
            "receivable_types": self._get_related_names(
                invoice.rows.all(), "receivable_type"
            ),
            "tenant": tenant_names,
            "share_numerator": tenant.share_numerator if tenant else None,
            "share_denominator": tenant.share_denominator if tenant else None,
            "billing_contact": billing_names,
            "intended_uses": self._get_related_names(
                invoice.rows.all(), "intended_use"
            ),
            "intended_use_note": lease.intended_use_note,
            "sent_to_sap_at": (
                timezone.localtime(invoice.sent_to_sap_at).replace(tzinfo=None)
                if invoice.sent_to_sap_at
                else None
            ),
            "invoice_type": str(invoice.type),
            "rent_types": self._get_attribute_values(lease.rents.all(), "type"),
            "rent_cycles": self._get_attribute_values(lease.rents.all(), "cycle"),
        }

    @staticmethod
    def get_total_amount_including_vat(lease: Lease, invoice: Invoice):
        if lease.is_subject_to_vat:
            return invoice.total_amount * VAT_MULTIPLIER
        return invoice.total_amount

    @staticmethod
    def _get_contact_names(contacts: list[Contact], contact_type):
        return ", ".join(
            contact.contact.get_name()
            for contact in contacts
            if contact.type == contact_type
        )

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
