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
        # # # Muistiinpanoja kyselystä # # # #
        #
        # Arvot jotka otetaan suoraan taulusta MV_KAAVAYKSIKON RAKOIKJAKAUMA (eli A):
        # - A.kg_kkaavyks (Käytetään joinissa. Ei tallenneta meillä mihinkään. Mitä tarkoittaa kg?)
        # - A.c_kaavayksikkotunnus (Käytetään lajitteluun. Ei tallenneta meillä mihinkään)
        # - A.c_paasivuk (Ei käytetä muualla kyselyssä, eikä tallenneta meillä mihinkään. Mitä tarkoittaa paasivuk? Onko edes tarpeen?)
        # - A.c_rakoikeus (Tämä on se rakennusoikeuden määrä, tallennetaan usage_distribution.build_permission)
        #
        # Pöydästä mv_koodisto otetaan rivit mukaan vain kun:
        # - mv_koodisto0.c_koodisto on 'SU_KAYTJAKAUMA' ja samalla mv_koodisto0.c_koodi on sama kuin A.c_kaytjakauma
        #
        # Pöydästä mv_kaavayksikko otetaan rivit mukaan vain kun:
        # - mv_kaavayksikko.kg_kkaavyks on sama kuin A.kg_kkaavyks
        #
        # - mv_koodisto0 alias ei taida olla tarpeellinen tässä kyselyssä, koska ei ole vaaraa sekoittaa sitä toiseen samannimiseen tauluun (ellei ole Oracle-kohtainen seikka?)
        # - LEFT OUTER JOIN voisi olla pelkkä LEFT JOIN, koska Oraclessa ne ovat sama asia
        #
        # Käyttöoikeusjakauman tunniste/koodi c_kaytjakauma (meillä usage_distribution.distribution) on:
        # - A.c_kaytjakauma jos se ei ole '1'.
        # - mv_kaavayksikko.c_kayttota jos se ei ole null ja A.c_kaytjakauma on '1'
        # - '1' jos sekä A.c_kaytjakauma ja mv_kaavayksikko.c_kayttota ovat null
        # --> Esimerkiksi: 1A, 1AC, 1C, 1N, 2, 2A, 2AB, 2AC, 2P, 2Ö, 3, ... , 7K
        #
        # Selitteen mv_koodisto0_c_selite (ei tallenneta meillä, onko tarpeen?) arvo on:
        # - mv_koodisto0.c_selite jos A.c_kaytjakauma arvo ei ole  '1', tai jos A.c_kaytjakauma arvo on '1' ja samalla mv_kaavayksikko.ktarsel on null
        # - mv_kaavayksikko.c_ktarsel jos se ei ole null ja A.c_kaytjakauma  on '1'

        # # # # Lisää kysymyksiä joita selvittää Factan vastauksista # # # #
        #
        # - Saadaanko me jakaumat ja niille rakennusoikeuden määrät kun jakaumia on vain 1?
        # - Mistä me saadaan rakennusoikeuden määrä, jos Facta ei tarjoa sitä tässä kyselyssä kun jakaumia on tasan 1?
        #   Onko haluttu rakennusoikeuden määrä meillä tallennettuna johonkin muuhun tauluun eri tietueen nimellä?

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
                        # UsageDistribution.objects.get_or_create(
                        #     plan_unit=plan_unit,
                        #     distribution=usage_distribution_row["C_KAYTJAKAUMA"] or "-",
                        #     build_permission=usage_distribution_row["C_RAKOIKEUS"]
                        #     or "-",
                        # )
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
