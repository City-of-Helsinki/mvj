from django.conf import settings

import cx_Oracle
from leasing.models import Asset, Lease


def get_cursor():
    dsn_tns = cx_Oracle.makedsn(
        settings.LEGACY_HOST,
        settings.LEGACY_PORT,
        settings.LEGACY_SERVICES,
    )

    connection = cx_Oracle.connect(
        user=settings.LEGACY_USER,
        password=settings.LEGACY_PASSWORD,
        dsn=dsn_tns,
    )
    return connection.cursor()


def import_table(importer, table_name):
    cursor = get_cursor()
    cursor.execute("SELECT count(*) FROM %s" % table_name)
    total = cursor.fetchone()[0]
    cursor.execute("SELECT * FROM %s" % table_name)
    i = 0

    for row in cursor:
        importer(row)
        i += 1
        percent = round(i/total*100, 1)
        print('Importing', table_name, str(percent) + '%\r', end='')
    print('')


def import_lease(row):
    lease, created = Lease.objects.get_or_create(
        type=row[0],
        municipality=row[1],
        district=row[2],
        # row[3] skipped on purpose
        sequence=row[4],
        start_date=row[15],
        end_date=row[16],
    )
    return lease


def import_asset(row):
    asset, created = Asset.objects.get_or_create(
        type=row[1],
        surface_area=row[2],
        address=row[3],
    )
    return asset


IMPORTERS_AND_TABLE_NAMES = [
    (import_lease, 'vuokraus'),
    (import_asset, 'vuokrakohde'),
]


def run_import():
    for method, table_name in IMPORTERS_AND_TABLE_NAMES:
        import_table(method, table_name)
