import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

import cx_Oracle
from leasing.enums import (
    ContactType, DueDatesPosition, DueDatesType, IndexType, InvoiceDeliveryMethod, InvoiceState, InvoiceType,
    LeaseAreaType, LeaseState, LocationType, PeriodType, RentAdjustmentAmountType, RentAdjustmentType, RentCycle,
    RentType, TenantContactType)
from leasing.models import (
    Contact, ContractRent, District, FixedInitialYearRent, IndexAdjustedRent, IntendedUse, Invoice, Lease, LeaseArea,
    LeaseIdentifier, LeaseType, Municipality, PayableRent, Rent, RentAdjustment, RentIntendedUse, Tenant, TenantContact)
from leasing.models.invoice import InvoiceRow
from leasing.models.land_area import LeaseAreaAddress
from leasing.models.rent import FIXED_DUE_DATES, RentDueDate
from leasing.models.utils import DayMonth


def expand_lease_identifier(id):
    return {
        'id': id,
        'ALKUOSA': id[:id.index('-')],
        'TARKOITUS': id[0:2],
        'KUNTA': int(id[2:3]),
        'KAUPOSA': int(id[3:5]),
        'JUOKSU': int(id[id.index('-') + 1:])
    }


def expanded_id_to_query(expanded_id):
    return """
AND TARKOITUS = '{TARKOITUS}'
AND KUNTA = {KUNTA}
AND KAUPOSA = {KAUPOSA}
AND JUOKSU = {JUOKSU}
""".format(**expanded_id)


def expanded_id_to_query_alku(expanded_id):
    return """
AND ALKUOSA = '{ALKUOSA}'
AND JUOKSU = {JUOKSU}
""".format(**expanded_id)


def rows_to_dict_list(cursor):
    columns = [i[0] for i in cursor.description]
    return [dict(zip(columns, row)) for row in cursor]


VUOKRALAJI_MAP = {
    # TODO: Is MANUAL the correct default
    None: RentType.MANUAL,
    '1': RentType.FIXED,
    '2': RentType.INDEX,
    '3': RentType.ONE_TIME,
    '4': RentType.FREE,
    '5': RentType.MANUAL,
}

TILA_MAP = {
    'V': LeaseState.LEASE,
    'H': LeaseState.APPLICATION,
    'L': LeaseState.PERMISSION,
    'R': LeaseState.RESERVATION,
    'S': LeaseState.TRANSFERRED,
    'T': LeaseState.FREE,
}

VUOKRAKAUSI_MAP = {
    None: None,
    '1': RentCycle.JANUARY_TO_DECEMBER,
    '2': RentCycle.APRIL_TO_MARCH,
}

ALENNUS_KOROTUS_MAP = {
    'A': RentAdjustmentType.DISCOUNT,
    'K': RentAdjustmentType.INCREASE,
}

# Values from receivable_type.json fixture
SAAMISLAJI_MAP = {
    'VU': 1,
    'KO': 2,
}

LASKUN_TILA_MAP = {
    'H': InvoiceState.REFUNDED,
    'A': InvoiceState.OPEN,
    'S': InvoiceState.PAID,
}

LASKUTYYPPI_MAP = {
    'V': InvoiceType.CHARGE,
    'H': InvoiceType.CREDIT_NOTE,
}

ASIAKASTYYPPI_MAP = {
    None: ContactType.OTHER,
    '0': ContactType.PERSON,
    '1': ContactType.BUSINESS,
    '2': ContactType.UNIT,
    '3': ContactType.ASSOCIATION,
    '4': ContactType.OTHER,
}

IRTISANOMISAIKA_MAP = {
    '01': 3,  # 2 viikon irtisanomisaika
    '02': 7,  # 1 kk:n irtisanomisaika
    '03': 8,  # 2 kk:n irtisanomisaika
    '04': 9,  # 3 kk:n irtisanomisaika
    '10': 16,  # muu irtisanomisaika
    '05': 10,  # 6 kk:n irtisanomisaika
    '06': 13,  # 1 vuoden irtisanomisaika
    '07': 14,  # 2 vuoden irtisanomisaika
    '08': 12,  # 15 kkn irtisanomisaika
    '09': 15,  # 3 vuoden irtisanomisaika
    '11': 2,  # 1 viikon irtisanomisaika
    '12': 4,  # 3 viikon irtisanomisaika
    '13': 1,  # Ei irtisanomisaikaa (mm.rasite
    '14': 6,  # 30 päivän irtisanomisaika
    '15': 11,  # 9 kk:n irtisanomisaika
    '16': 5,  # 14 vuorok. irtisanomisaika
}

HITAS_MAP = {
    '0': 2,  # Ei hitasta
    '1': 3,  # Hitas I
    '2': 4,  # Hitas II
    '3': 5,  # Laatusääntely
    '4': 6,  # Ei laatusääntelyä
    '6': 8,  # Ei tietoa
    '7': 9,  # Hitas II (Loikkari)
    '8': 10,  # Hitas (vapautettu)
    '9': 11,  # Hintakontrolloitu
    'A': 1,  # Puolihitas
}

FINANCING_MAP = {
    '0': 5,  # Ei tietoa
    '1': 6,  # Aravalainoitettu
    '2': 7,  # Vapaarahoitteinen
    '3': 8,  # Peruskorjauslaina
    '4': 9,  # Korkotuki
    '5': 10,  # Arava tai korkotuki
    '6': 11,  # Vapaarah. tai arava
    '7': 12,  # Vap.rah. tai korkot.
    '8': 13,  # Korkot./arava/vap.ra
    '9': 14,  # Muu kuin AV ja p. KT
    'A': 1,  # Korkotuki yht. pitkä
    'B': 2,  # Korkotuki yht. lyhyt
    'C': 3,  # Korkotuki osakk. om.
    'D': 4,  # Muu
}

MANAGEMENT_MAP = {
    '0': 6,  # Ei tieoa
    '1': 7,  # Omistus
    '2': 8,  # Vuokra
    '3': 9,  # Asumisoikeus
    '4': 10,  # Sekatalo
    '5': 11,  # Vuokra tai asumisoik
    '6': 12,  # Omistus tai vuokra
    '7': 13,  # Omist./vuokra/as.oik
    '8': 14,  # Osaomistus
    '9': 15,  # Asumisoik./osaomist.
    'A': 1,  # koe
    'B': 2,  # koe 2
    'C': 3,  # Asumisoikeus/omistus
    'D': 4,  # Asumisoikeus/vuokra
    'E': 5,  # Omistus ja vuokra
}

LEASE_AREA_TYPE_MAP = {
    None: LeaseAreaType.OTHER,  # Unknown
    '1': LeaseAreaType.PLAN_UNIT,  # Kaavatontti
    '2': LeaseAreaType.REAL_PROPERTY,  # Kiinteistö
    '3': LeaseAreaType.OTHER,  # Siirtolapuutarhapalsta
}

asiakas_cache = {}


class Command(BaseCommand):
    help = 'Import data from the old MVJ'

    def get_or_create_contact(self, data, unknown_contact):
        if data['ASIAKAS']:
            if data['ASIAKAS'] in asiakas_cache:
                return asiakas_cache[data['ASIAKAS']]

            contact_type = ASIAKASTYYPPI_MAP[data['ASIAKASTYYPPI']]
            name = None
            first_name = None
            last_name = None

            if contact_type == ContactType.PERSON:
                last_name = data['NIMI'].split(' ', 1)[0]
                try:
                    first_name = data['NIMI'].split(' ', 1)[1]
                except IndexError:
                    pass
            else:
                name = data['NIMI']

            (contact, contact_created) = Contact.objects.get_or_create(type=contact_type, first_name=first_name,
                                                                       last_name=last_name, name=name,
                                                                       address=data['OSOITE'],
                                                                       postal_code=data['POSTINO'],
                                                                       business_id=data['LYTUNNUS'])
        else:
            self.stdout.write('ASIAKAS #{} missing.')
            contact = unknown_contact

        asiakas_cache[data['ASIAKAS']] = contact

        return contact

    def handle(self, *args, **options):  # noqa: C901 'Command.handle' is too complex
        (unknown_contact, unknown_contact_created) = Contact.objects.get_or_create(
            type=ContactType.OTHER,
            first_name='Unknown',
            last_name='Unknown',
            name='Unknown'
        )

        connection = cx_Oracle.connect(user='mvj', password='mvjpass', dsn='localhost:1521/ORCLPDB1')

        cursor = connection.cursor()

        lease_ids = [
            'S0159-5',  # kiinteä vuosivuokra.
            'S0154-529',  # kiinteä kuukausivuokra.
            'A1149-382',  # indeksivuokra. Tässä on nykyisin käytettävä indeksilaskentatapa ilman alennuksia.
            'A1127-30',  # Indeksivuokraus, jossa alennus.
            'A1154-878',  # Indeksivuokraus, jossa kaksi sopimusvuokraa, mutta vain toista koskee alennus.
            # random:
            'O1133-28',
            'A1129-198',
            'S0110-92',
            'A1134-432',
            'A1134-430',
            'A1136-348',
            'S0123-170',
            'V2149-3',
            'S0120-219',
            'A4123-35',
            'K0136-23',
            # 'S0135-55',  # Liian uusi
            'T1155-1',
            'A1110-223',
        ]

        # lease_ids = ['A1149-382']
        # lease_ids = ['A4123-35']
        # lease_ids = ['A1136-348']

        query = """
            SELECT ALKUOSA, JUOKSU
            FROM VUOKRAUS
            WHERE ALKUPVM >= TO_DATE('01/01/2016', 'DD/MM/YYYY')
              AND ALKUPVM < TO_DATE('01/01/2017', 'DD/MM/YYYY')
            ORDER BY ALKUPVM
            """
        cursor.execute(query)
        lease_ids = ['{}-{}'.format(row[0], row[1]) for row in cursor]

        lease_id_count = len(lease_ids)
        self.stdout.write('{} lease ids'.format(lease_id_count))

        # LEASE_TYPE_MAP = {lt.identifier: lt.id for lt in LeaseType.objects.all()}
        intended_use_map = {intended_use.name: intended_use.id for intended_use in IntendedUse.objects.all()}

        count = 0
        for lease_id in lease_ids:
            if not lease_id:
                continue

            count += 1
            self.stdout.write('{} ({}/{})'.format(lease_id, count, lease_id_count))

            id_parts = expand_lease_identifier(lease_id)

            # self.stdout.write(expanded_id_to_query(id_parts))

            asiakas_num_to_tenant = {}

            query = """
                SELECT v.*, k.NIMI AS KTARK_NIMI
                FROM VUOKRAUS v
                LEFT JOIN KTARK_KOODI k ON v.KTARK_KOODI = k.KTARK_KOODI
                WHERE 1 = 1
                """ + expanded_id_to_query(id_parts)

            cursor.execute(query)

            vuokraus_rows = rows_to_dict_list(cursor)

            for lease_row in vuokraus_rows:
                # self.stdout.write(lease_row)
                lease_type = LeaseType.objects.get(identifier=id_parts['TARKOITUS'])
                municipality = Municipality.objects.get(identifier=id_parts['KUNTA'])
                district = District.objects.get(municipality=municipality, identifier=id_parts['KAUPOSA'])

                (lease_identifier, lease_identifier_created) = LeaseIdentifier.objects.get_or_create(
                    type=lease_type, municipality=municipality, district=district, sequence=id_parts['JUOKSU'])

                if lease_identifier_created:
                    lease = Lease.objects.create(
                        type=lease_type,
                        municipality=municipality,
                        district=district,
                        identifier=lease_identifier,
                    )
                else:
                    lease = Lease.objects.get(identifier=lease_identifier)

                lease.state = TILA_MAP[lease_row['TILA']]
                lease.start_date = lease_row['ALKUPVM'].date() if lease_row['ALKUPVM'] else None
                lease.end_date = lease_row['LOPPUPVM'].date() if lease_row['LOPPUPVM'] else None
                lease.intended_use_id = intended_use_map[lease_row['KTARK_NIMI']] if lease_row[
                    'KTARK_NIMI'] in intended_use_map else None
                lease.intended_use_note = lease_row['KTARK_TXT']
                lease.notice_period_id = IRTISANOMISAIKA_MAP[lease_row['IRTISANOMISAIKA']] if lease_row[
                    'IRTISANOMISAIKA'] else None
                lease.notice_note = lease_row['IRTISAN_KOMM']
                lease.reference_number = lease_row['DIAARINO']
                lease.hitas_id = HITAS_MAP[lease_row['HITAS']] if lease_row['HITAS'] else None
                lease.financing_id = FINANCING_MAP[lease_row['RAHOITUSM']] if lease_row['RAHOITUSM'] else None
                lease.management_id = MANAGEMENT_MAP[lease_row['HALLINTAM']] if lease_row['HALLINTAM'] else None

                if lease_row['SIIRTO_OIKEUS'] == 'K':
                    lease.transferable = True
                elif lease_row['SIIRTO_OIKEUS'] == 'E':
                    lease.transferable = False

                lease.is_invoicing_enabled = True if lease_row['LASKUTUS'] == 'K' else False

                lease.save()

                self.stdout.write("Vuokralaiset:")
                query = """
                    SELECT ar.*, a.*
                    FROM ASROOLI ar
                    LEFT JOIN ASIAKAS a ON ar.ASIAKAS = a.ASIAKAS
                    WHERE 1 = 1
                    """ + expanded_id_to_query_alku(id_parts)

                cursor.execute(query)
                asrooli_rows = rows_to_dict_list(cursor)

                for role_row in [row for row in asrooli_rows if row['ROOLI'] == 'V']:
                    self.stdout.write(" ASIAKAS V #{}".format(role_row['ASIAKAS']))
                    contact = self.get_or_create_contact(role_row, unknown_contact)
                    self.stdout.write('  Contact {}'.format(contact))

                    try:
                        tenant = lease.tenants.get(tenantcontact__contact=contact,
                                                   tenantcontact__type=TenantContactType.TENANT,
                                                   tenantcontact__start_date=role_row['ALKAEN'],
                                                   tenantcontact__end_date=role_row['SAAKKA'])
                        self.stdout.write("  USING EXISTING TENANT")
                    except ObjectDoesNotExist:
                        self.stdout.write("  TENANT DOES NOT EXIST. Creating.")
                        tenant = Tenant.objects.create(
                            lease=lease,
                            share_numerator=role_row['HALLINTAOSUUS_O'],
                            share_denominator=role_row['HALLINTAOSUUS_N']
                        )

                    (tenantcontact, tenantcontact_created) = TenantContact.objects.get_or_create(
                        type=TenantContactType.TENANT,
                        tenant=tenant,
                        contact=contact,
                        start_date=role_row['ALKAEN'],
                        end_date=role_row['SAAKKA']
                    )

                    asiakas_num_to_tenant[role_row['ASIAKAS']] = tenant

                for role_row in [row for row in asrooli_rows if row['ROOLI'] in ('L', 'Y')]:
                    self.stdout.write(" ASIAKAS {} #{}".format(role_row['ROOLI'], role_row['ASIAKAS']))
                    contact = self.get_or_create_contact(role_row, unknown_contact)
                    self.stdout.write('  Contact {}'.format(contact))

                    this_tenant = None
                    for lease_tenant in lease.tenants.all():
                        for lease_tenantcontact in lease_tenant.tenantcontact_set.all():
                            try:
                                if lease_tenantcontact.contact == asiakas_cache[role_row['LIITTYY_ASIAKAS']]:
                                    this_tenant = lease_tenant
                            except KeyError:
                                self.stdout.write('  LIITTYY_ASIAKAS {} not one of the tenants! Skipping.'.format(
                                    role_row['LIITTYY_ASIAKAS']))

                    if this_tenant:
                        (tenantcontact, tenantcontact_created) = TenantContact.objects.get_or_create(
                            type=TenantContactType.BILLING if role_row['ROOLI'] == 'L' else TenantContactType.CONTACT,
                            tenant=this_tenant,
                            contact=contact,
                            start_date=role_row['ALKAEN'],
                            end_date=role_row['SAAKKA']
                        )

                        asiakas_num_to_tenant[role_row['ASIAKAS']] = this_tenant

                query = """
                    SELECT sv.*, kt.NIMI as kt_nimi
                    FROM SOPIMUSVUOKRA sv
                    LEFT JOIN KAYTTOTARKOITUS kt ON sv.KAYTTOTARKOITUS = kt.KAYTTOTARKOITUS
                    WHERE 1 = 1
                    """ + expanded_id_to_query_alku(id_parts)

                cursor.execute(query)
                sopimusvuokra_rows = rows_to_dict_list(cursor)

                self.stdout.write("Vuokra:")
                rent_type = VUOKRALAJI_MAP[lease_row['VUOKRALAJI']]
                rent_cycle = VUOKRAKAUSI_MAP[lease_row['VUOKRAKAUSI']]
                try:
                    index_type = IndexType['TYPE_{}'.format(lease_row['INDEKSITUNNUS'])]
                except KeyError:
                    index_type = None

                (rent, rent_created) = Rent.objects.get_or_create(lease=lease, type=rent_type, cycle=rent_cycle,
                                                                  index_type=index_type)

                rent.x_value = lease_row['X_LUKU']
                rent.y_value = lease_row['Y_LUKU']

                if lease_row['Y_KK'] and lease_row['Y_VVVV']:
                    rent.y_value_start = datetime.date(year=lease_row['Y_VVVV'], month=lease_row['Y_KK'], day=1)

                rent.equalization_start_date = lease_row['TASAUS_ALKUPVM']
                rent.equalization_end_date = lease_row['TASAUS_LOPPUPVM']
                rent.save()

                # Due dates
                self.stdout.write("Epäpäivät:")
                if lease_row['LASKUJEN_LKM_VUODESSA']:
                    rent.due_dates_type = DueDatesType.FIXED
                    rent.due_dates_per_year = 12
                    rent.save()
                    self.stdout.write(" DUE DATES FIXED {} per year".format(rent.due_dates_per_year))
                else:
                    query = """
                        SELECT *
                        FROM VUOKRAUKSEN_ERAPAIVA
                        WHERE 1 = 1
                        """ + expanded_id_to_query_alku(id_parts)

                    cursor.execute(query)
                    vuokrauksen_erapaiva_rows = rows_to_dict_list(cursor)

                    due_dates_match_found = False
                    due_dates = set()
                    for due_date_row in vuokrauksen_erapaiva_rows:
                        due_dates.add(DayMonth.from_datetime(due_date_row['ERAPVM']))

                    if due_dates:
                        for due_dates_per_year, due_dates_set in FIXED_DUE_DATES[
                                DueDatesPosition.START_OF_MONTH].items():
                            if due_dates == set(due_dates_set):
                                rent.due_dates_type = DueDatesType.FIXED
                                rent.due_dates_per_year = due_dates_per_year
                                due_dates_match_found = True
                                if lease.type.due_dates_position != DueDatesPosition.MIDDLE_OF_MONTH:
                                    self.stdout.write(" WARNING! Wrong due dates type")
                                break

                        for due_dates_per_year, due_dates_set in FIXED_DUE_DATES[
                                DueDatesPosition.MIDDLE_OF_MONTH].items():
                            if due_dates == set(due_dates_set):
                                rent.due_dates_type = DueDatesType.FIXED
                                rent.due_dates_per_year = due_dates_per_year
                                due_dates_match_found = True
                                if lease.type.due_dates_position != DueDatesPosition.MIDDLE_OF_MONTH:
                                    self.stdout.write(" WARNING! Wrong due dates type")
                                break

                        if not due_dates_match_found:
                            self.stdout.write(" DUE DATES MATCH NOT FOUND. Adding custom dates:")
                            self.stdout.write(" {}".format(due_dates))
                            rent.due_dates_type = DueDatesType.CUSTOM
                            rent.due_dates.set([])
                            for due_date in due_dates:
                                RentDueDate.objects.create(rent=rent, day=due_date.day, month=due_date.month)
                        else:
                            self.stdout.write(" DUE DATES FOUND. {} per year".format(rent.due_dates_per_year))

                        rent.save()
                    else:
                        self.stdout.write(' NO DUE DATES IN "VUOKRAUKSEN_ERAPAIVA"')

                initial_rent = None
                if lease_row['KIINTEA_ALKUVUOSIVUOKRAN_MAARA'] and lease_row['KIINTEA_ALKUVUOSIVUOKRAN_LOPPU']:
                    (initial_rent, initial_rent_created) = FixedInitialYearRent.objects.get_or_create(
                        rent=rent,
                        amount=lease_row['KIINTEA_ALKUVUOSIVUOKRAN_MAARA'],
                        start_date=lease_row['ALKUPVM'] if lease_row['ALKUPVM'] else None,
                        end_date=lease_row['KIINTEA_ALKUVUOSIVUOKRAN_LOPPU'])

                self.stdout.write("Sopimusvuokrat:")
                for rent_row in sopimusvuokra_rows:
                    contract_rent_amount = None
                    contract_rent_period = None
                    if rent_row['SOPIMUSVUOKRA_VUOSI']:
                        contract_rent_amount = rent_row['SOPIMUSVUOKRA_VUOSI']
                        contract_rent_period = PeriodType.PER_YEAR

                    if rent_row['SOPIMUSVUOKRA_KK']:
                        contract_rent_amount = rent_row['SOPIMUSVUOKRA_KK']
                        contract_rent_period = PeriodType.PER_MONTH

                    try:
                        contract_rent_intended_use = RentIntendedUse.objects.get(pk=rent_row['KAYTTOTARKOITUS'])
                    except RentIntendedUse.DoesNotExist:
                        (contract_rent_intended_use, _) = RentIntendedUse.objects.get_or_create(
                            id=rent_row['KAYTTOTARKOITUS'], name=rent_row['KT_NIMI'])

                    (contract_rent, contract_rent_created) = ContractRent.objects.get_or_create(
                        rent=rent, period=contract_rent_period, intended_use=contract_rent_intended_use,
                        defaults={
                            'amount': contract_rent_amount,
                            'base_amount': rent_row['PERUSVUOKRA'] if rent_row['PERUSVUOKRA'] else contract_rent_amount,
                            'base_amount_period': contract_rent_period,
                            'start_date': rent_row['ALKUPVM'].date() if rent_row['ALKUPVM'] else None,
                            'end_date': rent_row['LOPPUPVM'].date() if rent_row['LOPPUPVM'] else None,
                        }
                    )

                    # TODO: No intended use for initial year rent in the old system
                    if initial_rent and not initial_rent.intended_use_id:
                        initial_rent.intended_use = contract_rent_intended_use
                        initial_rent.save()

                self.stdout.write("Tarkistettu vuokra:")

                query = """
                    SELECT *
                    FROM TARKISTETTU_VUOKRA
                    WHERE 1 = 1
                    """ + expanded_id_to_query_alku(id_parts)

                cursor.execute(query)
                tarkistettu_vuokra_rows = rows_to_dict_list(cursor)

                for rent_row in tarkistettu_vuokra_rows:
                    (ia_rent, ia_rent_created) = IndexAdjustedRent.objects.get_or_create(
                        rent=rent,
                        amount=rent_row['TARKISTETTU_VUOKRA'],
                        intended_use_id=int(rent_row['KAYTTOTARKOITUS']),
                        start_date=rent_row['ALKUPVM'].date() if rent_row['ALKUPVM'] else None,
                        end_date=rent_row['LOPPUPVM'].date() if rent_row['LOPPUPVM'] else None,
                        factor=rent_row['LASKENTAKERROIN'],
                    )

                self.stdout.write("Perittävä vuokra:")

                query = """
                    SELECT *
                    FROM VUOSIVUOKRA
                    WHERE 1 = 1
                    """ + expanded_id_to_query_alku(id_parts)

                cursor.execute(query)
                vuosivuokra_rows = rows_to_dict_list(cursor)

                for rent_row in vuosivuokra_rows:
                    (payable_rent, payable_rent_created) = PayableRent.objects.get_or_create(
                        rent=rent,
                        amount=rent_row['PERITTAVAVUOKRA'],
                        calendar_year_rent=rent_row['KALENTERIVUOSIVUOKRA'] if rent_row['KALENTERIVUOSIVUOKRA'] else 0,
                        start_date=rent_row['ALKUPVM'].date() if rent_row['ALKUPVM'] else None,
                        end_date=rent_row['LOPPUPVM'].date() if rent_row['LOPPUPVM'] else None,
                        difference_percent=rent_row['NOUSUPROSENTTI'] if rent_row['NOUSUPROSENTTI'] else 0,
                    )

                self.stdout.write("Alennus:")

                query = """
                    SELECT *
                    FROM ALENNUS
                    WHERE 1 = 1
                    """ + expanded_id_to_query_alku(id_parts)

                cursor.execute(query)
                alennus_rows = rows_to_dict_list(cursor)

                for adjustment_row in alennus_rows:
                    adjustment_type = ALENNUS_KOROTUS_MAP[adjustment_row['ALENNUS_KOROTUS']]

                    if adjustment_row['ALE_MK']:
                        amount_type = RentAdjustmentAmountType.AMOUNT_PER_YEAR
                        full_amount = adjustment_row['ALE_MK']

                    if adjustment_row['ALE_PROS']:
                        amount_type = RentAdjustmentAmountType.PERCENT_PER_YEAR
                        full_amount = adjustment_row['ALE_PROS']

                    (adjustment, adjustment_created) = RentAdjustment.objects.get_or_create(
                        rent=rent,
                        type=adjustment_type,
                        intended_use_id=int(adjustment_row['KAYTTOTARKOITUS']),
                        start_date=adjustment_row['ALKUPVM'].date() if adjustment_row['ALKUPVM'] else None,
                        end_date=adjustment_row['LOPPUPVM'].date() if adjustment_row['LOPPUPVM'] else None,
                        full_amount=full_amount,
                        amount_type=amount_type,
                        amount_left=None,
                        decision=None,
                        note=adjustment_row['KOMMENTTITXT']
                    )

                # self.stdout.write("Alennushistoria:")
                #
                # query = """
                #     SELECT *
                #     FROM ALENNUS_HISTORIA
                #     WHERE 1 = 1
                #     """ + expanded_id_to_query_alku(id_parts)
                #
                # cursor.execute(query)
                # alennus_rows = rows_to_dict_list(cursor)
                #
                # for adjustment_row in alennus_rows:
                #     adjustment_type = ALENNUS_KOROTUS_MAP[adjustment_row['ALENNUS_KOROTUS']]
                #
                #     if adjustment_row['ALE_MK']:
                #         amount_type = RentAdjustmentAmountType.AMOUNT_PER_YEAR
                #         full_amount = adjustment_row['ALE_MK']
                #
                #     if adjustment_row['ALE_PROS']:
                #         amount_type = RentAdjustmentAmountType.PERCENT_PER_YEAR
                #         full_amount = adjustment_row['ALE_PROS']
                #
                #     # History rows might have an ending time, but the
                #     # row hasn't been in use when it has been moved
                #     # to the history table
                #     end_date = adjustment_row['MUUTOSPVM'].date()
                #     if adjustment_row['LOPPUPVM'] and adjustment_row['LOPPUPVM'].date() < adjustment_row[
                #         'MUUTOSPVM'].date():
                #         end_date = adjustment_row['MUUTOSPVM'].date()
                #
                #     (adjustment, adjustment_created) = RentAdjustment.objects.get_or_create(
                #         rent=rent,
                #         type=adjustment_type,
                #         intended_use_id=int(adjustment_row['KAYTTOTARKOITUS']),
                #         start_date=adjustment_row['ALKUPVM'].date() if adjustment_row['ALKUPVM'] else None,
                #         end_date=end_date,
                #         full_amount=full_amount,
                #         amount_type=amount_type,
                #         amount_left=None,
                #         decision=None,
                #         note=adjustment_row['KOMMENTTITXT']
                #     )

                self.stdout.write("Lasku:")

                query = """
                    SELECT l.*, a.*, l.ASIAKAS AS LASKU_ASIAKAS
                    FROM R_LASKU l
                    LEFT JOIN ASIAKAS a ON l.ASIAKAS = a.ASIAKAS
                    WHERE 1 = 1
                    """ + expanded_id_to_query(id_parts)

                cursor.execute(query)
                lasku_rows = rows_to_dict_list(cursor)

                for invoice_row in lasku_rows:
                    if invoice_row['ASIAKAS']:
                        contact_type = ASIAKASTYYPPI_MAP[invoice_row['ASIAKASTYYPPI']]
                        name = None
                        first_name = None
                        last_name = None

                        if contact_type == ContactType.PERSON:
                            last_name = invoice_row['NIMI'].split(' ', 1)[0]
                            try:
                                first_name = invoice_row['NIMI'].split(' ', 1)[1]
                            except IndexError:
                                pass
                        else:
                            name = invoice_row['NIMI']

                        (contact, contact_created) = Contact.objects.get_or_create(
                            type=contact_type,
                            first_name=first_name,
                            last_name=last_name,
                            name=name,
                            address=invoice_row['OSOITE'],
                            postal_code=invoice_row['POSTINO'],
                            business_id=invoice_row['LYTUNNUS'],
                        )
                    else:
                        self.stdout.write('ASIAKAS #{} in Invoice #{} missing. Using unkown_contact.'.format(
                            invoice_row['LASKU_ASIAKAS'], invoice_row['LASKU']
                        ))
                        contact = unknown_contact

                    receivable_type_id = SAAMISLAJI_MAP[invoice_row['SAAMISLAJI']]
                    invoice_state = LASKUN_TILA_MAP[invoice_row['LASKUN_TILA']]
                    invoice_type = LASKUTYYPPI_MAP[invoice_row['LASKUTYYPPI']]

                    period_start_date = invoice_row['LASKUTUSKAUSI_ALKAA'] if invoice_row[
                        'LASKUTUSKAUSI_ALKAA'] else lease.start_date
                    period_end_date = invoice_row['LASKUTUSKAUSI_PAATTYY'] if invoice_row[
                        'LASKUTUSKAUSI_PAATTYY'] else lease.end_date

                    if not period_end_date:
                        period_end_date = period_start_date

                    (invoice, invoice_created) = Invoice.objects.get_or_create(
                        lease=lease,
                        recipient=contact,
                        due_date=invoice_row['ERAPVM'],
                        state=invoice_state,
                        billing_period_start_date=period_start_date,
                        billing_period_end_date=period_end_date,
                        invoicing_date=invoice_row['LASKUTUSPVM'],
                        postpone_date=invoice_row['LYKKAYSPVM'],
                        total_amount=invoice_row['LASKUN_PAAOMA'],
                        billed_amount=invoice_row['LASKUTETTU_MAARA'],
                        paid_amount=invoice_row['LASKUTETTU_MAARA'] - invoice_row['MAKSAMATON_MAARA'],  # TODO
                        paid_date=None,  # TODO
                        outstanding_amount=invoice_row['MAKSAMATON_MAARA'],
                        payment_notification_date=invoice_row['MAKSUKEHOITUSPVM1'],
                        collection_charge=invoice_row['PERINTAKULU1'],
                        payment_notification_catalog_date=invoice_row['MAKSUKEHLUETAJOPVM1'],
                        delivery_method=InvoiceDeliveryMethod.MAIL,
                        type=invoice_type,
                        notes='',  # TODO
                        generated=True,  # TODO
                    )

                    (invoice_row, invoice_row_created) = InvoiceRow.objects.get_or_create(
                        invoice=invoice,
                        tenant=asiakas_num_to_tenant[
                            invoice_row['ASIAKAS']] if invoice_row['ASIAKAS'] in asiakas_num_to_tenant else None,
                        receivable_type_id=receivable_type_id,
                        billing_period_start_date=period_start_date,
                        billing_period_end_date=period_end_date,
                        amount=invoice_row['LASKUN_OSUUS']
                    )

                    if period_end_date.year != period_start_date.year:
                        invoice.billing_period_end_date = datetime.date(
                            year=period_start_date.year, month=period_end_date.month, day=period_end_date.day)
                        invoice.save()

                self.stdout.write('Vuokra-alue:')

                query = """
                    SELECT *
                    FROM HALLINTA h
                    LEFT JOIN VUOKRAKOHDE k ON k.KOHDE = h.KOHDE
                    WHERE 1 = 1
                    """ + expanded_id_to_query_alku(id_parts)

                cursor.execute(query)
                kohde_rows = rows_to_dict_list(cursor)

                for lease_area_row in kohde_rows:
                    identifier = '{}-{}-{}-{}'.format(lease_area_row['KUNTATUNNUS'], lease_area_row['KAUPOSATUNNUS'],
                                                      lease_area_row['KORTTELI'], lease_area_row['TONTTI'])
                    if lease_area_row['MVJ_PALSTA'] != '000':
                        identifier += '-{}'.format(lease_area_row['MVJ_PALSTA'])

                    (lease_area, lease_area_created) = LeaseArea.objects.get_or_create(
                        lease=lease,
                        type=LEASE_AREA_TYPE_MAP[lease_area_row['KIINTEISTOTYYPPI']],
                        identifier=identifier,
                        area=lease_area_row['PINTA_ALA_M2'] if lease_area_row['PINTA_ALA_M2'] else 0,
                        section_area=lease_area_row['PINTA_ALA_M2'] if lease_area_row['PINTA_ALA_M2'] else 0,
                        location=LocationType.SURFACE,
                    )

                    if lease_area_row['OSOITE']:
                        (lease_area_address, lease_area_address_created) = LeaseAreaAddress.objects.get_or_create(
                            lease_area=lease_area,
                            address=lease_area_row['OSOITE'],
                        )

                self.stdout.write('*****\n\n')
