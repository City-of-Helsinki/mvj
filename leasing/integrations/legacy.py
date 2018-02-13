from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

import cx_Oracle
from leasing.models import Asset, Client, ClientLanguage, ClientRole, ClientType, Lease, PhoneNumber

orphans = {
    "lease_and_asset_relations_leases": [],
    "lease_and_asset_relations_assets": [],
    "client_roles": [],
}


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
    orphaned = False

    lease_id = row[0] + '-' + str(row[1])
    asset_id = row[2]

    lease = None
    asset = None

    try:
        lease = Lease.objects.get_from_identifier(lease_id)
    except ObjectDoesNotExist:
        orphaned = True
        orphans["lease_and_asset_relations_leases"].append(lease_id)

    try:
        asset = Asset.objects.get(legacy_id=asset_id)
    except ObjectDoesNotExist:
        orphaned = True
        orphans["lease_and_asset_relations_assets"].append(asset_id)

    if orphaned:
        return

    asset.leases.add(lease)


def import_clients(row):
    client_language = None
    client_type = None

    if row[5] is not None:
        client_language = ClientLanguage(int(row[5]))

    if row[16] is not None:
        client_type = ClientType(int(row[16]))

    client, created = Client.objects.get_or_create(
        legacy_id=row[0],
        name=row[1],
        address=row[2] or "",
        postal_code=row[3] or "",
        country=row[4] or "",
        language=client_language,
        # row[6] ignored on purpose
        business_id=row[7] or "",
        comment=row[15] or "",
        client_type=client_type,
        debt_collection=row[17] or "",
        partnership_code=row[18] or "",
        email=row[19] or "",
        trade_register=row[20] or "",
        # rows 21-28 ignored on purpose
        ssid=row[29] or "",
        # row 30 ignored on purpose (original data contains only nulls)
    )

    phone_strings = row[8:11]

    for string in phone_strings:
        if string is None:
            continue

        phone_number, created = PhoneNumber.objects.get_or_create(
            number=string
        )
        client.phone_numbers.add(phone_number)


def import_client_roles(row):
    orphaned = False

    client_id = row[0]
    lease_id = row[1] + "-" + str(row[2])
    related_client_id = row[9]

    client = None
    lease = None
    related_client = None

    try:
        lease = Lease.objects.get_from_identifier(lease_id)
    except ObjectDoesNotExist:
        orphaned = True

    try:
        client = Client.objects.get(legacy_id=client_id)
    except ObjectDoesNotExist:
        orphaned = True

    try:
        related_client = Client.objects.get(legacy_id=related_client_id)
    except ObjectDoesNotExist:
        orphaned = True

    if orphaned:
        orphans['client_roles'].append({
            "client_id": client_id,
            "lease_id": lease_id,
            "related_client_id": related_client_id
        })
        return

    client_role, created = ClientRole.objects.get_or_create(
        client=client,
        lease=lease,
        role_type=row[3],
        shares_numerator=row[4],
        shares_denominator=row[5],
        start_date=row[6],
        end_date=row[7],
        notification_method=row[8] or "",
        related_client=related_client
    )


IMPORTERS_AND_TABLE_NAMES = [
    (import_lease, 'vuokraus'),
    (import_asset, 'vuokrakohde'),
    (import_lease_and_asset_relations, 'hallinta'),
    (import_clients, 'asiakas'),
    (import_client_roles, 'asrooli'),
]


def run_import():
    for method, table_name in IMPORTERS_AND_TABLE_NAMES:
        import_table(method, table_name)
    print_report()


def print_report():
    print("Orphans found:")
    for key in orphans:
        value = orphans[key]
        print(len(value), key)
