from itertools import groupby
from typing import List

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

    def import_usage_distributions(self):
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

        # Ensure that the rows are ordered by C_KAAVAYKSIKKOTUNNUS for itertools.groupby()
        for row_plan_unit_identifier, usage_distributions_group in groupby(
            usage_distribution_rows, key=lambda row: row["C_KAAVAYKSIKKOTUNNUS"]
        ):
            plan_unit_identifier = self._strip_leading_zeros_from_identifier(
                row_plan_unit_identifier
            )

            plan_unit_qs = PlanUnit.objects.filter(identifier=plan_unit_identifier)
            # Make iterator a list so it can be reused
            grouped_usage_distributions_list = list(usage_distributions_group)

            for plan_unit in plan_unit_qs:
                # Usage distribution ids that existed already or were created
                existing_or_created_usage_distributions_ids: List[int] = []

                for usage_distribution_row in grouped_usage_distributions_list:
                    usage_distribution, _created = (
                        UsageDistribution.objects.get_or_create(
                            plan_unit=plan_unit,
                            distribution=usage_distribution_row["C_KAYTJAKAUMA"] or "-",
                            build_permission=usage_distribution_row["C_RAKOIKEUS"]
                            or "-",
                        )
                    )

                    existing_or_created_usage_distributions_ids.append(
                        usage_distribution.id
                    )

                redundant_usage_distributions = plan_unit.usage_distributions.exclude(
                    id__in=existing_or_created_usage_distributions_ids
                )
                redundant_usage_distributions.delete()

    def _strip_leading_zeros_from_identifier(self, identifier: str) -> str:
        """Strips leading zeros from identifiers joined by hyphens `-`
        e.g. '0001-0002' -> '1-2'"""
        plan_unit_id = "-".join(
            str(int(part)) for part in identifier.split("-")  # Strip leading zeros
        )
        return plan_unit_id
