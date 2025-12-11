import logging

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.postgres.aggregates import StringAgg
from django.core.management.base import BaseCommand
from django.db.models import (
    Case,
    Exists,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Sum,
    When,
)
from django.utils import timezone
from django_q.tasks import async_task
from rest_framework import serializers

from leasing.models.contract import Contract
from leasing.models.decision import Decision
from leasing.models.land_area import LeaseArea
from leasing.models.lease import Lease
from leasing.models.report_storage import ReportStorage

logger = logging.getLogger(__name__)

DATE_FORMAT = "%d.%m.%Y"  # 01.01.2025
DATETIME_FORMAT = "%d.%m.%Y %H:%M %z"  # 01.01.2025 12:00 +0200


class LeaseProcessingTimeReportSerializer(serializers.Serializer):
    palvelukokonaisuus = serializers.CharField(
        source="service_unit.name", allow_null=True, read_only=True
    )
    url = serializers.SerializerMethodField()
    vuokraustunnus = serializers.CharField(
        source="identifier.identifier", allow_null=True, read_only=True
    )
    vuokrauksen_luonti_pvm = serializers.DateTimeField(
        source="created_at", allow_null=True, read_only=True, format=DATETIME_FORMAT
    )
    kayttotarkoitus = serializers.CharField(
        source="intended_use.name", allow_null=True, read_only=True
    )
    vuokrauksen_alku_pvm = serializers.DateField(
        source="start_date", allow_null=True, read_only=True, format=DATE_FORMAT
    )
    vuokrauksen_loppu_pvm = serializers.DateField(
        source="end_date", allow_null=True, read_only=True, format=DATE_FORMAT
    )
    vuokrauksen_kokonaisala = serializers.IntegerField(
        source="total_lease_area", allow_null=True, read_only=True
    )
    vuokralaisten_tyypit = serializers.CharField(
        source="tenant_types", allow_null=True, read_only=True
    )
    kaupunginosa = serializers.CharField(
        source="district.identifier", allow_null=True, read_only=True
    )
    valmistelija = serializers.CharField(
        source="preparer.last_name", allow_null=True, read_only=True
    )
    allekirjoitus_pvm = serializers.DateField(
        source="latest_signing_date",
        allow_null=True,
        read_only=True,
        format=DATE_FORMAT,
    )
    laskutus_kaynnistetty_pvm = serializers.DateTimeField(
        source="invoicing_enabled_at",
        allow_null=True,
        read_only=True,
        format=DATETIME_FORMAT,
    )
    vuokratiedot_kunnossa_pvm = serializers.DateTimeField(
        source="rent_info_completed_at",
        allow_null=True,
        read_only=True,
        format=DATETIME_FORMAT,
    )
    geometria = serializers.IntegerField(
        source="geometria_value", allow_null=True, read_only=True
    )
    viimeisin_paatoksen_pvm = serializers.DateField(
        source="latest_decision_date",
        allow_null=True,
        read_only=True,
        format=DATE_FORMAT,
    )
    hakemuksen_saapumis_pvm = serializers.DateField(
        source="application_metadata.application_received_at",
        allow_null=True,
        read_only=True,
        format=DATE_FORMAT,
    )

    def get_url(self, obj: Lease):
        if getattr(settings, "OFFICER_UI_URL", "").endswith("/"):
            return f"{settings.OFFICER_UI_URL}vuokraukset/{obj.id}"
        return f"{settings.OFFICER_UI_URL}/vuokraukset/{obj.id}"


def get_lease_processing_time_report():

    now = timezone.now()
    two_years_back = now - relativedelta(years=2)

    has_geometry_subquery = Exists(
        LeaseArea.objects.filter(lease=OuterRef("pk"), geometry__isnull=False)
    )

    queryset = (
        Lease.objects.filter(deleted__isnull=True)
        .filter(Q(end_date__gte=two_years_back) | Q(end_date__isnull=True))
        .select_related("identifier", "district", "preparer", "application_metadata")
        .prefetch_related(
            "lease_areas",
            "intended_use",
            "identifier",
            "contracts",
            "tenants",
            "tenants__contacts",
            "service_unit",
        )
        .annotate(
            total_lease_area=Sum("lease_areas__area"),
            latest_signing_date=Subquery(
                Contract.objects.filter(lease=OuterRef("pk"))
                .order_by("-signing_date")
                .values("signing_date")[:1]
            ),
            latest_decision_date=Subquery(
                Decision.objects.filter(lease=OuterRef("pk"))
                .order_by("-decision_date")
                .values("decision_date")[:1]
            ),
            tenant_types=StringAgg(
                "tenants__contacts__type",
                delimiter=",",
                ordering="tenants__contacts__type",
            ),
            geometria_value=Case(
                When(has_geometry_subquery, then=1),
                default=0,
                output_field=IntegerField(),
            ),
        )
    )

    serializer = LeaseProcessingTimeReportSerializer(queryset, many=True)

    return serializer.data


class Command(BaseCommand):
    """
    Generate Lease processing time report
    In Finnish: Vuokrausten käsittelyaikojen raportti
    """

    help = "Generate Lease processing time report to ReportStorage"

    def handle(self, *args, **options):
        input_data = {}
        async_task_timeout = 60 * 60  # 1 hour
        try:
            async_task(handle_async_task, input_data, timeout=async_task_timeout)
        except Exception as e:
            logger.exception(f"Queuing async task for '{self.help}' failed: {e}")
        logger.info(f"Queued async task for '{self.help}'")


def handle_async_task(input_data):
    report_slug = "lease_processing_time"
    try:
        logger.info(f"Starting generation of {report_slug} report to ReportStorage")
        # Generate report data and create a ReportStorage
        report_data = get_lease_processing_time_report()

        ReportStorage.objects.create(
            report_data=report_data,
            input_data=input_data,
            report_type=report_slug,
        )
    except Exception as e:
        logger.exception(
            f"Generation of {report_slug} report to ReportStorage failed: {e}"
        )
        raise e

    # Delete one month old ReportStorage objects for report `lease_processing_time`
    one_month_ago = timezone.now() - relativedelta(months=1)
    deleted_count, _ = ReportStorage.objects.filter(
        report_type=report_slug, created_at__lt=one_month_ago
    ).delete()
    logger.info(
        f"Deleted {deleted_count} old ReportStorage objects for report `{report_slug}`"
    )
    logger.info("Generation of Lease processing time report to ReportStorage done")
