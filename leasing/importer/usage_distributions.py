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
        from auditlog.registry import auditlog

        # Unregister all models from auditlog when importing
        for model in list(auditlog._registry.keys()):
            auditlog.unregister(model)

        self.import_usage_distributions()

    def import_usage_distributions(self):
        self.initialize_importer()
        cursor = self.cursor

        # Note: selite is not saved to MVJ, but is helpful for understanding the Facta output.
        query = """
        SELECT DISTINCT
            COALESCE(A.kg_kkaavyks, B.kg_kkaavyks) AS kg_kkaavyks,
            COALESCE(A.c_kaavayksikkotunnus, B.kaavayksikko) AS kaavayksikkotunnus,
            COALESCE(NULLIF(A.c_kaytjakauma, '1'), B.c_kayttota, A.c_kaytjakauma) AS c_kaytjakauma,
            CASE
                WHEN A.c_kaytjakauma = '1' THEN COALESCE(B.c_ktarsel, C.c_selite)
                ELSE C.c_selite
            END AS selite,
            A.c_rakoikeus,
            B.i_rakoikeus
        FROM MV_KAAVAYKSIKON_RAKOIKJAKAUMA A
        LEFT OUTER JOIN mv_koodisto C ON (A.c_kaytjakauma=C.c_koodi AND C.c_koodisto='SU_KAYTJAKAUMA')
        FULL OUTER JOIN mv_kaavayksikko B ON A.kg_kkaavyks = B.kg_kkaavyks
        ORDER BY kaavayksikkotunnus ASC
        """

        cursor.execute(query)

        usage_distribution_rows = rows_to_dict_list(cursor)

        # Ensure that the rows are ordered by C_KAAVAYKSIKKOTUNNUS for itertools.groupby()
        for row_plan_unit_identifier, usage_distributions_group in groupby(
            usage_distribution_rows, key=lambda row: row["KAAVAYKSIKKOTUNNUS"]
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
                            build_permission=self._get_build_permission_value(
                                usage_distribution_row
                            ),
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
        """
        Strips leading zeros from identifiers joined by hyphens `-`
        e.g. '0001-0002' -> '1-2'
             '0123-0000' -> '123-0'
        """
        plan_unit_id = "-".join(
            str(int(part)) for part in identifier.split("-")  # Strip leading zeros
        )
        return plan_unit_id

    def _get_build_permission_value(
        self, usage_distribution_row: dict[str, str]
    ) -> str:
        """
        Primarily, use the usage distribution's build permission.

        If that value is None, use plan unit's build permission instead.
        This can happen if the plan unit doesn't have usage distributions,
        but we still want to know how much build permission is available in
        total.

        If even that value is None, return a string signifying a missing value.
        """
        usage_distribution_build_permission = usage_distribution_row["C_RAKOIKEUS"]
        plan_unit_build_permission = usage_distribution_row["I_RAKOIKEUS"]

        if usage_distribution_build_permission is not None:
            return usage_distribution_build_permission
        elif (
            usage_distribution_build_permission is None
            and plan_unit_build_permission is not None
        ):
            return plan_unit_build_permission
        else:
            return "-"
