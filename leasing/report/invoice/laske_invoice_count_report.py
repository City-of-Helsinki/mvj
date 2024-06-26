import datetime
from collections import Counter
from typing import List, Optional, TypedDict

from dateutil.relativedelta import relativedelta
from django import forms
from django.db.models import Q
from django.db.models.aggregates import Count
from django.db.models.functions.datetime import TruncDate
from django.utils.timezone import make_aware, now
from django.utils.translation import gettext_lazy as _

from leasing.models import Invoice, Rent, ServiceUnit
from leasing.report.report_base import ReportBase


class InputData(TypedDict):
    service_unit: Optional[List[int]]
    start_date: datetime.date
    end_date: datetime.date


class LaskeInvoiceCountReport(ReportBase):
    name = _("Count of Invoices sent to Laske per day")
    description = _(
        "Shows actual sent invoice counts until yesterday, and estimated counts for today and beyond"
    )
    slug = "laske_invoice_count"
    input_fields = {
        "service_unit": forms.ModelMultipleChoiceField(
            label=_("Service unit"),
            queryset=ServiceUnit.objects.all(),
            required=False,
        ),
        "start_date": forms.DateField(label=_("Start date"), required=True),
        "end_date": forms.DateField(label=_("End date"), required=True),
    }
    output_fields = {
        "send_date": {"label": _("Send date"), "format": "date"},
        "invoice_count": {"label": _("Invoice count"), "is_numeric": True},
        "estimate_count": {"label": _("Estimated invoice count"), "is_numeric": True},
    }

    def _generate_invoice_counter_with_date_keys(
        self, query_start_date: datetime.date, query_end_date: datetime.date
    ):
        invoice_counter: Counter = Counter()
        tmp_date = query_start_date
        while tmp_date < query_end_date:
            invoice_counter[tmp_date] = 0
            tmp_date += datetime.timedelta(days=1)
        return invoice_counter

    def _get_invoice_counts(
        self,
        original_invoice_counter: Counter,
        query_start_date: datetime.date,
        query_end_date: datetime.date,
        input_data: InputData,
    ):
        invoice_counter = original_invoice_counter.copy()
        invoice_qs = (
            Invoice.objects.annotate(send_date=TruncDate("sent_to_sap_at"))
            .filter(
                sent_to_sap_at__gte=make_aware(
                    datetime.datetime.combine(query_start_date, datetime.time(0, 0))
                ),
                sent_to_sap_at__lte=make_aware(
                    datetime.datetime.combine(query_end_date, datetime.time(23, 59))
                ),
            )
            .values("send_date")
            .annotate(invoice_count=Count("id"))
            .order_by("send_date")
        )

        if input_data["service_unit"]:
            invoice_qs = invoice_qs.filter(service_unit__in=input_data["service_unit"])

        for invoice in invoice_qs:
            invoice_counter[invoice["send_date"]] = invoice["invoice_count"]

        return invoice_counter

    def _get_estimate_counts(
        self,
        original_invoice_counter: Counter,
        today: datetime.date,
        estimate_start_date: datetime.date,
        estimate_end_date: datetime.date,
        input_data: InputData,
    ):
        invoice_counter = original_invoice_counter.copy()
        due_dates_start = estimate_start_date + relativedelta(months=1)
        due_dates_end = estimate_end_date + relativedelta(months=1)

        # Create estimated counts for upcoming rents
        rents = (
            Rent.objects.filter(
                (Q(end_date__isnull=True) | Q(end_date__gte=estimate_start_date))
            )
            .filter(lease__end_date__gte=today, lease__is_invoicing_enabled=True)
            .select_related("lease", "lease__type")
        )

        if input_data["service_unit"]:
            rents = rents.filter(lease__service_unit__in=input_data["service_unit"])

        for rent in rents:
            due_dates = rent.get_due_dates_for_period(due_dates_start, due_dates_end)

            for due_date in due_dates:
                invoice_counter[due_date - relativedelta(months=1)] += 1

        # Create estimated counts for invoices not yet sent to SAP
        invoices = Invoice.objects.filter(
            due_date__lte=due_dates_end,
            due_date__gte=due_dates_start,
            sent_to_sap_at__isnull=True,
        )

        if input_data["service_unit"]:
            invoices = invoices.filter(
                lease__service_unit__in=input_data["service_unit"]
            )

        for invoice in invoices:
            invoice_counter[invoice.due_date - relativedelta(months=1)] += 1

        return invoice_counter

    def get_data(self, input_data: InputData):
        today = now().date()
        query_start_date: datetime.date | None = min(
            input_data["start_date"], input_data["end_date"]
        )
        query_end_date: datetime.date | None = max(
            input_data["end_date"], input_data["start_date"]
        )

        if query_start_date is not None and query_end_date is not None:
            invoice_counter = self._generate_invoice_counter_with_date_keys(
                query_start_date, query_end_date
            )
        else:
            raise ValueError("Start date and end date must be provided")

        estimate_start_date = None
        estimate_end_date = None

        if query_start_date is not None and query_start_date > today:
            # Query is in future, only estimates can be provided
            estimate_start_date = query_start_date
            query_start_date = None
            estimate_end_date = query_end_date
            query_end_date = None
        elif query_end_date is not None and query_end_date > today:
            # Query ends in future, provide estimates for dates after today
            estimate_start_date = today
            estimate_end_date = query_end_date
            query_end_date = today

        if query_start_date and query_end_date:
            invoice_counter = self._get_invoice_counts(
                invoice_counter, query_start_date, query_end_date, input_data
            )

        if estimate_start_date and estimate_end_date:
            invoice_counter = self._get_estimate_counts(
                invoice_counter,
                today,
                estimate_start_date,
                estimate_end_date,
                input_data,
            )

        send_dates = []
        for send_date, invoice_count in invoice_counter.items():
            if invoice_count == 0:
                continue
            is_estimate = send_date > today
            if is_estimate:
                send_dates.append(
                    {
                        "send_date": send_date,
                        "invoice_count": 0,
                        "estimate_count": invoice_count,
                    },
                )
            else:
                send_dates.append(
                    {
                        "send_date": send_date,
                        "invoice_count": invoice_count,
                        "estimate_count": 0,
                    },
                )
        return send_dates
