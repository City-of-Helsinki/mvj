from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from leasing.models.report_storage import ReportStorage
from leasing.report.lease.lease_statistic_report import LeaseStatisticReport


class Command(BaseCommand):
    """
    Generate Lease statistic report
    """

    help = "Generate Lease statistic report to ReportStorage"

    def handle(self, *args, **options):
        lease_statistics_report = LeaseStatisticReport()
        previous_year = timezone.now().year - 1
        input_data = {
            "service_unit": None,
            # Start of the previous year
            "start_date": f"{previous_year}-01-01",
            "end_date": None,
            "state": None,
            "only_active_leases": None,
        }
        try:
            # Generate report data and create a ReportStorage
            report_data = lease_statistics_report.get_data(input_data)
            serialized_report_data = lease_statistics_report.serialize_data(report_data)
            ReportStorage.objects.create(
                report_data=serialized_report_data,
                input_data=input_data,
                report_type="lease_statistic",
            )
        except Exception as e:
            self.stdout.write(
                f"Generation of Lease Statistic report to ReportStorage failed: {e}"
            )

        # Delete one month old ReportStorage objects for report `lease_statistic`
        one_month_ago = timezone.now() - relativedelta(months=1)
        deleted_count, _ = ReportStorage.objects.filter(
            report_type="lease_statistic", created_at__lt=one_month_ago
        ).delete()
        self.stdout.write(
            f"Deleted {deleted_count} old ReportStorage objects for report `lease_statistic`"
        )
        self.stdout.write("Generation of Lease Statistic report to ReportStorage done")
