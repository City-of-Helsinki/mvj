from django.db import connection

from leasing.enums import LeaseRelationType
from leasing.models import RelatedLease

from .base import BaseImporter
from .utils import rows_to_dict_list


class LeaseRelationsImporter(BaseImporter):
    type_name = 'lease_relations'

    def __init__(self, stdout=None, stderr=None):
        import cx_Oracle
        connection = cx_Oracle.connect(user='mvj', password='mvjpass', dsn='localhost:1521/ORCLPDB1', encoding="UTF-8",
                                       nencoding="UTF-8")

        self.cursor = connection.cursor()
        self.stdout = stdout
        self.stderr = stderr
        self.offset = 0

    @classmethod
    def add_arguments(cls, parser):
        pass

    def read_options(self, options):
        pass

    def execute(self):  # noqa: C901 'Command.handle' is too complex
        from auditlog.registry import auditlog

        # Unregister model from auditlog when importing
        auditlog.unregister(RelatedLease)

        lease_identifier_to_id = {}
        with connection.cursor() as django_cursor:
            django_cursor.execute("""
            SELECT l.id, lt.identifier leasetype, lm.identifier municipality, ld.identifier district, li.sequence
            FROM leasing_lease l
            JOIN leasing_leaseidentifier li ON l.identifier_id = li.id
            JOIN leasing_leasetype lt on li.type_id = lt.id
            JOIN leasing_municipality lm on li.municipality_id = lm.id
            JOIN leasing_district ld on li.district_id = ld.id
            ORDER BY lt.identifier, lm.identifier, ld.identifier, li.sequence
            """)

            for row in django_cursor.fetchall():
                identifier = '{}{}{:02}-{}'.format(row[1], row[2], int(row[3]), row[4])
                lease_identifier_to_id[identifier] = row[0]

        cursor = self.cursor

        query = """
            SELECT * FROM (
                SELECT ALKUOSA, JUOKSU, LIITTYY_ALKUOSA, LIITTYY_JUOKSU, ROW_NUMBER() OVER (ORDER BY ALKUOSA, JUOKSU) rn
                FROM VUOKRAUS
                WHERE LIITTYY_ALKUOSA != ALKUOSA OR LIITTYY_JUOKSU != JUOKSU
                AND TILA != 'S'
                ORDER BY ALKUOSA, JUOKSU
            ) t
            WHERE rn >= {}
            """.format(self.offset)

        cursor.execute(query)

        vuokraus_rows = rows_to_dict_list(cursor)
        vuokraus_count = len(vuokraus_rows)

        self.stdout.write('{} relations'.format(vuokraus_count))

        count = 0
        found = 0
        for lease_row in vuokraus_rows:
            count += 1

            from_lease = "{}-{}".format(lease_row['LIITTYY_ALKUOSA'], lease_row['LIITTYY_JUOKSU'])
            to_lease = "{}-{}".format(lease_row['ALKUOSA'], lease_row['JUOKSU'])

            try:
                from_lease_id = lease_identifier_to_id[from_lease]
            except KeyError:
                self.stderr.write('From lease "{}" not found.'.format(from_lease))
                continue

            try:
                to_lease_id = lease_identifier_to_id[to_lease]
            except KeyError:
                self.stderr.write('To lease "{}" not found.'.format(to_lease))
                continue

            self.stdout.write(' {} #{} -> {} #{}'.format(from_lease, from_lease_id, to_lease, to_lease_id))

            found += 1
            (related_lease, related_lease_created) = RelatedLease.objects.get_or_create(
                from_lease_id=from_lease,
                to_lease_id=to_lease,
                type=LeaseRelationType.OTHER,
            )

        self.stdout.write('{}/{} found'.format(found, count))
