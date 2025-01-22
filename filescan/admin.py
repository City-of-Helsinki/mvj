from django.contrib import admin

from .models import FileScanStatus


@admin.register(FileScanStatus)
class FileScanStatusAdmin(admin.ModelAdmin):
    list_display = (
        "filepath",
        "scanned_at",
        "file_deleted_at",
        "error_message",
        "scan_result",
    )
    search_fields = ("filepath",)
    list_filter = ("scanned_at", "file_deleted_at", "content_type", "error_message")

    # Dynamically set all fields as read-only
    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields] + ["scan_result"]

    def scan_result(self, scan_status: FileScanStatus) -> str:
        return scan_status.scan_result().value

    scan_result.short_description = "Scan result"
