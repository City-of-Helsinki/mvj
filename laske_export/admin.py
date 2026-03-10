from django.contrib.gis import admin
from django.db.models import Count
from django.forms import BaseInlineFormSet
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from laske_export.models import LaskeExportLog, LaskePaymentsLog


class NoDeleteInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_delete = False


class InvoiceInline(admin.TabularInline):
    model = LaskeExportLog.invoices.through
    readonly_fields = (
        "invoice_number",
        "due_date",
        "lease",
        "status",
        "service_unit",
        "information",
    )
    exclude = ("invoice",)
    raw_id_fields = ("invoice",)
    formset = NoDeleteInlineFormSet
    extra = 0
    verbose_name = _("Invoice")
    verbose_name_plural = _("Invoices")

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related(
            "invoice__lease__type",
            "invoice__lease__municipality",
            "invoice__lease__district",
            "invoice__lease__identifier",
            "invoice__lease__identifier__type",
            "invoice__lease__identifier__municipality",
            "invoice__lease__identifier__district",
            "invoice__service_unit",
        )

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(
        description=_("Lease identifier")
    )
    def lease(self, obj):
        return obj.invoice.lease.get_identifier_string()


    @admin.display(
        description=_("Invoice number")
    )
    def invoice_number(self, obj):
        invoice_url = reverse(
            "admin:{}_{}_change".format(
                obj.invoice._meta.app_label, obj.invoice._meta.model_name
            ),
            args=(obj.invoice.pk,),
        )

        return mark_safe(
            '<a target="_blank" href="{}">{}</a>'.format(
                invoice_url, obj.invoice.number
            )
        )


    @admin.display(
        description=_("Due date")
    )
    def due_date(self, obj):
        return obj.invoice.due_date


    @admin.display(
        description=_("Service unit")
    )
    def service_unit(self, obj):
        return obj.invoice.service_unit



@admin.register(LaskeExportLog)
class LaskeExportLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "invoice_count",
        "started_at",
        "ended_at",
        "is_finished",
        "service_unit",
    )
    readonly_fields = (
        "id",
        "started_at",
        "ended_at",
        "is_finished",
        "service_unit",
        "filename",
    )
    inlines = [InvoiceInline]
    exclude = ("invoices",)
    search_fields = ["filename", "invoices__number"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.annotate(
            invoice_count=Count("invoices"),
        )

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(
        description=_("Invoice count")
    )
    def invoice_count(self, obj):
        return obj.invoice_count



class InvoicePaymentInline(admin.TabularInline):
    model = LaskePaymentsLog.payments.through
    readonly_fields = (
        "invoice_number",
        "paid_amount",
        "paid_date",
        "filing_code",
        "lease",
        "service_unit",
    )
    exclude = ("invoicepayment",)
    raw_id_fields = ("invoicepayment",)
    formset = NoDeleteInlineFormSet
    extra = 0
    verbose_name = _("Invoice payment")
    verbose_name_plural = _("Invoice payments")

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related(
            "invoicepayment__invoice__lease__type",
            "invoicepayment__invoice__lease__municipality",
            "invoicepayment__invoice__lease__district",
            "invoicepayment__invoice__lease__identifier",
            "invoicepayment__invoice__lease__identifier__type",
            "invoicepayment__invoice__lease__identifier__municipality",
            "invoicepayment__invoice__lease__identifier__district",
            "invoicepayment__invoice__service_unit",
        )

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(
        description=_("Lease identifier")
    )
    def lease(self, obj):
        return obj.invoicepayment.invoice.lease.get_identifier_string()


    @admin.display(
        description=_("Invoice number")
    )
    def invoice_number(self, obj):
        invoice_url = reverse(
            "admin:{}_{}_change".format(
                obj.invoicepayment.invoice._meta.app_label,
                obj.invoicepayment.invoice._meta.model_name,
            ),
            args=(obj.invoicepayment.invoice.pk,),
        )

        return mark_safe(
            '<a target="_blank" href="{}">{}</a>'.format(
                invoice_url, obj.invoicepayment.invoice.number
            )
        )


    @admin.display(
        description=_("Paid amount")
    )
    def paid_amount(self, obj):
        return obj.invoicepayment.paid_amount


    @admin.display(
        description=_("Paid date")
    )
    def paid_date(self, obj):
        return obj.invoicepayment.paid_date


    @admin.display(
        description=_("Service unit")
    )
    def service_unit(self, obj):
        return obj.invoicepayment.invoice.service_unit


    @admin.display(
        description=_("Filing code")
    )
    def filing_code(self, obj):
        return obj.invoicepayment.filing_code



@admin.register(LaskePaymentsLog)
class LaskePaymentsLogAdmin(admin.ModelAdmin):
    list_display = ("id", "payment_count", "started_at", "ended_at", "is_finished")
    readonly_fields = ("id", "started_at", "ended_at", "is_finished", "filename")
    inlines = [InvoicePaymentInline]
    exclude = ("payments",)
    search_fields = ["filename", "payments__invoice__number", "payments__filing_code"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.annotate(
            payment_count=Count("payments"),
        )

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(
        description=_("Payment count")
    )
    def payment_count(self, obj):
        return obj.payment_count



