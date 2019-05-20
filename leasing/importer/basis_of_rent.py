import cx_Oracle  # isort:skip (Not installed in CI or production)

from leasing.models import BasisOfRent, BasisOfRentDecision, BasisOfRentPropertyIdentifier, BasisOfRentRate, Index

from .base import BaseImporter
from .mappings import (
    BASIS_OF_RENT_BUILD_PERMISSION_MAP, BASIS_OF_RENT_PLOT_TYPE_MAP, BASIS_OF_RENT_RATE_AREA_UNIT_MAP,
    DECISION_MAKER_MAP, FINANCING_MAP, MANAGEMENT_MAP)
from .utils import get_real_property_identifier, rows_to_dict_list


class BasisOfRentImporter(BaseImporter):
    type_name = 'basis_of_rent'

    def __init__(self, stdout=None, stderr=None):
        connection = cx_Oracle.connect(user='mvj', password='mvjpass', dsn='localhost:1521/ORCLPDB1', encoding="UTF-8",
                                       nencoding="UTF-8")

        self.cursor = connection.cursor()
        self.stdout = stdout
        self.stderr = stderr
        self.offset = 0

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument('--offset2', dest='offset', type=int, required=False,
                            help='basis of rent start offset')

    def read_options(self, options):
        if options['offset']:
            self.offset = options['offset']

    def execute(self):  # noqa: C901 'Command.handle' is too complex
        from auditlog.registry import auditlog

        # Unregister all models from auditlog when importing
        for model in list(auditlog._registry.keys()):
            auditlog.unregister(model)

        cursor = self.cursor

        query = """
            SELECT * FROM (
                SELECT p.*, ROW_NUMBER() OVER (ORDER BY ALKUPVM) rn
                FROM PERUSTE p
                ORDER BY ALKUPVM
            ) t
            WHERE rn >= {}
            """.format(self.offset)

        cursor.execute(query)

        peruste_rows = rows_to_dict_list(cursor)

        peruste_count = len(peruste_rows)

        count = 0
        if self.offset:
            count = self.offset - 1
            peruste_count += self.offset

        self.stdout.write('{} basis of rent rows'.format(peruste_count))

        for basis_of_rent_row in peruste_rows:
            count += 1
            self.stdout.write('PERUSTE #{} ({}/{})'.format(basis_of_rent_row['PERUSTE'], count, peruste_count))

            if basis_of_rent_row['KORTTELI'] is None:
                self.stdout.write(' KORTTELI missing. Skipping.')
                continue

            index = None
            if basis_of_rent_row['KK'] and basis_of_rent_row['VUOSI']:
                try:
                    index = Index.objects.get(month=basis_of_rent_row['KK'], year=basis_of_rent_row['VUOSI'])
                except Index.DoesNotExist:
                    self.stdout.write('Index VUOSI {} KK {} does not exist!'.format(basis_of_rent_row['VUOSI'],
                                                                                    basis_of_rent_row['KK']))

            notes = []
            if basis_of_rent_row['PERUSTETXT']:
                notes.append(basis_of_rent_row['PERUSTETXT'].strip())

            if basis_of_rent_row['ALENNUSTXT']:
                notes.append(basis_of_rent_row['ALENNUSTXT'].strip())

            (basis_of_rent, created) = BasisOfRent.objects.get_or_create(
                plot_type_id=BASIS_OF_RENT_PLOT_TYPE_MAP[basis_of_rent_row['TONTTITYYPPI']],
                start_date=basis_of_rent_row['ALKUPVM'].date() if basis_of_rent_row['ALKUPVM'] else None,
                end_date=basis_of_rent_row['LOPPUPVM'].date() if basis_of_rent_row['LOPPUPVM'] else None,
                detailed_plan_identifier=basis_of_rent_row['KAAVANO'],
                financing_id=FINANCING_MAP[basis_of_rent_row['RAHOITUSMUOTO']] if basis_of_rent_row[
                    'RAHOITUSMUOTO'] else None,
                management_id=MANAGEMENT_MAP[basis_of_rent_row['HALLINTAMUOTO']] if basis_of_rent_row[
                    'HALLINTAMUOTO'] else None,
                lease_rights_end_date=basis_of_rent_row['VUOKRAUSOIKEUSPVM'].date() if basis_of_rent_row[
                    'VUOKRAUSOIKEUSPVM'] else None,
                index=index,
                note='\n\n'.join(notes) if notes else None,
            )

            property_identifier = get_real_property_identifier(basis_of_rent_row)

            (basis_of_rent_property_identifier, created) = BasisOfRentPropertyIdentifier.objects.get_or_create(
                basis_of_rent=basis_of_rent, identifier=property_identifier)

            decision_column_prefixes = ['KLK', 'MUU']

            for decision_column_prefix in decision_column_prefixes:
                decision_maker_string = basis_of_rent_row['{}_PAATTAJA'.format(decision_column_prefix)]
                decision_datetime = basis_of_rent_row['{}_PAATOSPVM'.format(decision_column_prefix)]
                decision_section_string = basis_of_rent_row['{}_PYKALA'.format(decision_column_prefix)]

                if not decision_maker_string or not decision_datetime:
                    continue

                (basis_of_rent_decision, created) = BasisOfRentDecision.objects.get_or_create(
                    basis_of_rent=basis_of_rent,
                    reference_number=None,  # TODO
                    decision_maker_id=DECISION_MAKER_MAP[decision_maker_string] if decision_maker_string else None,
                    decision_date=decision_datetime.date() if decision_datetime else None,
                    section=decision_section_string if decision_section_string else None,
                )

            query = """
                SELECT *
                FROM PERUSTE_HINNAT
                WHERE PERUSTE = {}
                """.format(basis_of_rent_row['PERUSTE'])

            cursor.execute(query)

            hinta_rows = rows_to_dict_list(cursor)

            for rate_row in hinta_rows:
                build_permission_type = BASIS_OF_RENT_BUILD_PERMISSION_MAP[
                    (rate_row['RAKENNUSOIKEUSTYYPPI'], rate_row['ERITTELY'])
                ]
                amount = rate_row['MUU_HINTA_ARVIO']
                area_unit = BASIS_OF_RENT_RATE_AREA_UNIT_MAP[rate_row['MUU_HINTA_YKS']]

                if not amount:
                    amount = rate_row['KLK_HINTA_ARVIO']
                    area_unit = BASIS_OF_RENT_RATE_AREA_UNIT_MAP[rate_row['KLK_HINTA_YKS']]

                    if not amount:
                        amount = rate_row['HINTA_ARVIO']
                        area_unit = BASIS_OF_RENT_RATE_AREA_UNIT_MAP[rate_row['HINTA_YKS']]

                (basis_of_rent_rate, created) = BasisOfRentRate.objects.get_or_create(
                    basis_of_rent=basis_of_rent,
                    build_permission_type_id=build_permission_type,
                    amount=amount,
                    area_unit=area_unit,
                )
