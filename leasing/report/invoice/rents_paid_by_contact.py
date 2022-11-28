from django import forms
from django.utils.translation import ugettext_lazy as _

from leasing.enums import InvoiceType
from leasing.models import Contact, Invoice
from leasing.report.report_base import ReportBase


class RentsPaidByContactReport(ReportBase):
    name = _("Invoices paid by a contact")
    description = _("Show invoices paid by a contact")
    slug = "rents_paid_contact"
    input_fields = {
        "start_date": forms.DateField(label=_("Start date"), required=True),
        "end_date": forms.DateField(label=_("End date"), required=True),
        "contact_id": forms.IntegerField(label=_("Contact identifier"), required=True),
    }
    output_fields = {
        "contact_id": {"label": _("Contact identifier")},
        "name": {"label": _("Name")},
        "invoice_number": {"label": _("Invoice number")},
        "total_amount": {"label": _("Total amount"), "format": "money", "width": 13},
        "outstanding_amount": {
            "label": _("Outstanding amount"),
            "format": "money",
            "width": 13,
        },
        "invoicing_date": {"label": _("Invoicing date"), "format": "date"},
        "due_date": {"label": _("Due date"), "format": "date"},
        "n_rows": {"label": _("Number of rows")},
        "receivable_type": {"label": _("Receivable type")},
    }

    def get_data(self, input_data):
        try:
            contact = Contact.objects.get(pk=input_data["contact_id"])
        except Contact.DoesNotExist:
            return []

        aggregated_data = []
        invoices = (
            Invoice.objects.filter(
                recipient=contact,
                type=InvoiceType.CHARGE,
                total_amount__gt=0,
                invoicing_date__gte=input_data["start_date"],
                invoicing_date__lte=input_data["end_date"],
            )
            .prefetch_related("rows", "rows__receivable_type")
            .order_by("-due_date")
        )

        for invoice in invoices:
            name_str = (
                contact.name
                if contact.name
                else "{} {}".format(contact.first_name, contact.last_name)
            )
            aggregated_data.append(
                {
                    "contact_id": contact.id,
                    "name": name_str,
                    "invoice_number": invoice.number,
                    "total_amount": invoice.total_amount,
                    "outstanding_amount": invoice.outstanding_amount,
                    "invoicing_date": invoice.invoicing_date,
                    "due_date": invoice.due_date,
                    "n_rows": invoice.rows.count(),
                    "receivable_type": ", ".join(
                        {row.receivable_type.name for row in invoice.rows.all()}
                    ),
                }
            )

        return aggregated_data
