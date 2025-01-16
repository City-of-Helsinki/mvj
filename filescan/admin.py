# from django.contrib import admin

# from .models import FileScanStatus


# @admin.register(FileScanStatus)
# class FileScanStatusAdmin(admin.ModelAdmin):
#     list_display = (
#         "filename",
#         "content_type",
#         "object_id",
#         "scanned_at",
#         "deleted_at",
#         "error_message",
#         "scan_result",
#     )
#     search_fields = ("filename",)
#     list_filter = ("scanned_at", "deleted_at", "content_type", "error_message")
#     readonly_fields = ("scanned_at", "deleted_at", "error_message", "scan_result")

#     def scan_result(self, scan_status: FileScanStatus) -> str:
#         return scan_status.scan_result().value

#     scan_result.short_description = "Scan result"
