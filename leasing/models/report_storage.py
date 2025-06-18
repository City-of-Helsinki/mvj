from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class ReportStorage(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    report_data = models.JSONField(encoder=DjangoJSONEncoder)
    report_type = models.CharField(max_length=255)
    input_data = models.JSONField(null=True)

    class Meta:
        permissions = [
            (
                "export_api_lease_statistic_report",
                "Can access export API for lease statistics report",
            ),
            (
                "export_api_lease_processing_time_report",
                "Can access export API for lease processing time report",
            ),
        ]
