from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

import cx_Oracle
from leasing.models import Asset, Lease

orphan_leases = []
orphan_assets = []


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


@transaction.atomic
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
    # We probably want to skip all leases that have 'S' as their status in the
    # new database, as they are handled by another organization at the moment.
    if row[5] == 'S':
        return

    lease, created = Lease.objects.get_or_create(
        type=row[0],
        municipality=row[1],
        district=row[2],
        # row[3] skipped on purpose
        sequence=row[4],
        status=row[5],
        start_date=row[15],
        end_date=row[16],
    )
    return lease


def import_asset(row):
    asset, created = Asset.objects.get_or_create(
        legacy_id=row[0],
        type=row[1],
        surface_area=row[2],
        address=row[3],
    )
    return asset


def import_lease_and_asset_relations(row):
    lease_id = row[0] + '-' + str(row[1])
    asset_id = row[2]

    lease = None
    asset = None

    try:
        lease = Lease.objects.get_from_identifier(lease_id)
    except ObjectDoesNotExist:
        orphan_leases.append(lease_id)

    try:
        asset = Asset.objects.get(legacy_id=asset_id)
    except ObjectDoesNotExist:
        orphan_assets.append(asset_id)

    if not lease or not asset:
        return

    asset.leases.add(lease)


IMPORTERS_AND_TABLE_NAMES = [
    (import_lease, 'vuokraus'),
    (import_asset, 'vuokrakohde'),
    (import_lease_and_asset_relations, 'hallinta'),
]


def run_import():
    for method, table_name in IMPORTERS_AND_TABLE_NAMES:
        import_table(method, table_name)

    print_report()


def print_report():
    print(len(orphan_leases), 'orphan leases')
    print(len(orphan_assets), 'orphan assets')
