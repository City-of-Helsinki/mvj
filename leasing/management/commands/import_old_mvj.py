import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand

import cx_Oracle
from leasing.enums import (
    ContactType, IndexType, InvoiceDeliveryMethod, InvoiceState, InvoiceType, PeriodType, RentAdjustmentAmountType,
    RentAdjustmentType, RentCycle, RentType)
from leasing.models import (
    Contact, ContractRent, District, FixedInitialYearRent, IndexAdjustedRent, Invoice, Lease, LeaseIdentifier,
    LeaseType, Municipality, PayableRent, Rent, RentAdjustment, RentIntendedUse)


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
    None: None,
    '1': RentType.FIXED,
    '2': RentType.INDEX,
    '3': RentType.ONE_TIME,
    '4': RentType.FREE,
    '5': RentType.MANUAL,
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


class Command(BaseCommand):
    help = 'Import data from the old MVJ'

    def handle(self, *args, **options):
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
        ]

        # LEASE_TYPE_MAP = {lt.identifier: lt.id for lt in LeaseType.objects.all()}

        for lease_id in lease_ids:
            if not lease_id:
                continue

            self.stdout.write(lease_id)
            id_parts = expand_lease_identifier(lease_id)

            # self.stdout.write(expanded_id_to_query(id_parts))

            query = """
                SELECT *
                FROM VUOKRAUS
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

                lease.start_date = lease_row['ALKUPVM'].date() if lease_row['ALKUPVM'] else None
                lease.end_date = lease_row['LOPPUPVM'].date() if lease_row['LOPPUPVM'] else None
                lease.intended_use_note = lease_row['KTARK_TXT']
                lease.notice_period_id = IRTISANOMISAIKA_MAP[lease_row['IRTISANOMISAIKA']] if lease_row[
                    'IRTISANOMISAIKA'] else None
                lease.notice_note = lease_row['IRTISAN_KOMM']
                lease.save()

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

                self.stdout.write("Tarkistettu vuokra")

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
                        calendar_year_rent=rent_row['KALENTERIVUOSIVUOKRA'],
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

                    if invoice_row['LASKUN_PAAOMA'] > 0:
                        share_decimal = Decimal(invoice_row['LASKUN_OSUUS'] / invoice_row['LASKUN_PAAOMA'])
                    else:
                        share_decimal = Decimal(0)

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
                        receivable_type_id=receivable_type_id,
                        state=invoice_state,
                        billing_period_start_date=period_start_date,
                        billing_period_end_date=period_end_date,
                        invoicing_date=invoice_row['LASKUTUSPVM'],
                        postpone_date=invoice_row['LYKKAYSPVM'],
                        total_amount=invoice_row['LASKUN_PAAOMA'],
                        share_numerator=share_decimal.as_integer_ratio()[0],
                        share_denominator=share_decimal.as_integer_ratio()[1],
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
                    )

                    if period_end_date.year != period_start_date.year:
                        invoice.billing_period_end_date = datetime.date(
                            year=period_start_date.year, month=period_end_date.month, day=period_end_date.day)
                        invoice.save()
