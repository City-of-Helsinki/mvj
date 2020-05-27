from django.conf import settings
from django.contrib.gis import admin
from django.forms import BaseInlineFormSet
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from laske_export.models import LaskeExportLog


class NoDeleteInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_delete = False


class InvoiceInline(admin.TabularInline):
    model = LaskeExportLog.invoices.through
    readonly_fields = ("laskeexportlog", "invoice_number", "due_date", "lease")
    exclude = ("invoice",)
    raw_id_fields = ("invoice",)
    formset = NoDeleteInlineFormSet
    extra = 0
    verbose_name = _("Invoice")
    verbose_name_plural = _("Invoices")

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


class LaskeExportLogAdmin(admin.ModelAdmin):
    list_display = ("id", "started_at", "ended_at", "is_finished")
    readonly_fields = ("id", "started_at", "ended_at", "is_finished", "export_filename")
    inlines = [InvoiceInline]
    exclude = ("invoices",)
    search_fields = ["invoices__number"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def export_filename(self, obj):
        return "MTIL_IN_{}_{:08}.xml".format(settings.LASKE_VALUES["sender_id"], obj.id)


admin.site.register(LaskeExportLog, LaskeExportLogAdmin)
