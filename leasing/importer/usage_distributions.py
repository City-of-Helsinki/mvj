from django.conf import settings

from leasing.importer.base import BaseImporter
from leasing.importer.utils import rows_to_dict_list
from leasing.models import PlanUnit
from leasing.models.land_area import UsageDistribution


class UsageDistributionImporter(BaseImporter):
    type_name = "usage_distributions"

    def __init__(self, stdout=None, stderr=None):
        self.stdout = stdout
        self.stderr = stderr

    def initialize_importer(self):
        import oracledb

        connection = oracledb.connect(
            user=getattr(settings, "FACTA_DATABASE_USERNAME", None),
            password=getattr(settings, "FACTA_DATABASE_PASSWORD", None),
            dsn=getattr(settings, "FACTA_DATABASE_DSN", None),
        )

        self.cursor = connection.cursor()
        self.lease_ids = None
        self.offset = 0

    @classmethod
    def add_arguments(cls, parser):
        pass

    def read_options(self, options):
        pass

    def execute(self):
        from auditlog.registry import auditlog  # type: ignore

        # Unregister all models from auditlog when importing
        for model in list(auditlog._registry.keys()):
            auditlog.unregister(model)

        self.import_usage_distributions()

    def import_usage_distributions(self):  # noqa: C901 'Command.handle' is too complex
        self.initialize_importer()
        cursor = self.cursor
        query = """
        SELECT DISTINCT A.kg_kkaavyks,
            A.c_kaavayksikkotunnus,
            COALESCE(NULLIF(A.c_kaytjakauma, '1'), mv_kaavayksikko.c_kayttota, A.c_kaytjakauma) AS c_kaytjakauma,
            CASE
                WHEN A.c_kaytjakauma = '1' THEN COALESCE(mv_kaavayksikko.c_ktarsel, mv_koodisto0.c_selite)
                ELSE mv_koodisto0.c_selite
            END AS mv_koodisto0_c_selite,
            A.c_paasivuk,
            A.c_rakoikeus
        FROM MV_KAAVAYKSIKON_RAKOIKJAKAUMA A
        LEFT OUTER JOIN mv_koodisto mv_koodisto0 ON (A.c_kaytjakauma=mv_koodisto0.c_koodi AND mv_koodisto0.c_koodisto='SU_KAYTJAKAUMA')
        LEFT OUTER JOIN mv_kaavayksikko ON A.kg_kkaavyks = mv_kaavayksikko.kg_kkaavyks
        ORDER BY A.c_kaavayksikkotunnus ASC
        """

        cursor.execute(query)

        usage_distribution_rows = rows_to_dict_list(cursor)
        pivot_plan_unit = None

        for usage_distribution_row in usage_distribution_rows:
            plan_unit_id = "-".join(
                str(int(num))
                for num in usage_distribution_row["C_KAAVAYKSIKKOTUNNUS"].split("-")
            )

            plan_unit_qs = PlanUnit.objects.filter(identifier=plan_unit_id)
            if pivot_plan_unit is None:
                pivot_plan_unit = plan_unit_qs.first()
                if pivot_plan_unit is None:
                    continue
                pivot_plan_unit.usage_distributions.all().delete()

            for plan_unit in plan_unit_qs:
                if plan_unit.id != pivot_plan_unit.id:
                    plan_unit.usage_distributions.all().delete()
                    pivot_plan_unit = plan_unit

                UsageDistribution.objects.create(
                    plan_unit=plan_unit,
                    distribution=usage_distribution_row["C_KAYTJAKAUMA"] or "-",
                    build_permission=usage_distribution_row["C_RAKOIKEUS"] or "-",
                )
