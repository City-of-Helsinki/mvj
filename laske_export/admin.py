from django.contrib.gis import admin
from django.forms import BaseInlineFormSet
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from laske_export.models import LaskeExportLog


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

    def lease(self, obj):
        return obj.invoice.lease.get_identifier_string()

    lease.short_description = _("Lease")

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

    lease.short_description = _("Lease identifier")

    def due_date(self, obj):
        return obj.invoice.due_date

    due_date.short_description = _("Due date")

    def service_unit(self, obj):
        return obj.invoice.service_unit

    service_unit.short_description = _("Service unit")


class LaskeExportLogAdmin(admin.ModelAdmin):
    list_display = ("id", "started_at", "ended_at", "is_finished", "service_unit")
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

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(LaskeExportLog, LaskeExportLogAdmin)
