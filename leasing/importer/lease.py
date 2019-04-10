import datetime
import re
from decimal import ROUND_HALF_UP, Decimal

import cx_Oracle
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import make_aware

from leasing.enums import (
    ContactType, DueDatesPosition, DueDatesType, IndexType, InvoiceDeliveryMethod, LeaseRelationType, LeaseState,
    LocationType, PeriodType, RentAdjustmentAmountType, RentType, TenantContactType)
from leasing.models import (
    Collateral, Condition, Contact, Contract, ContractChange, ContractRent, Decision, District, FixedInitialYearRent,
    IndexAdjustedRent, Inspection, IntendedUse, Invoice, Lease, LeaseArea, LeaseIdentifier, LeaseType, Municipality,
    PayableRent, RelatedLease, Rent, RentAdjustment, RentIntendedUse, Tenant, TenantContact)
from leasing.models.invoice import InvoicePayment, InvoiceRow
from leasing.models.land_area import LeaseAreaAddress
from leasing.models.rent import FIXED_DUE_DATES, EqualizedRent, RentDueDate
from leasing.models.utils import DayMonth

from .base import BaseImporter
from .mappings import (
    ALENNUS_KOROTUS_MAP, DECISION_MAKER_MAP, FINANCING_MAP, HITAS_MAP, IRTISANOMISAIKA_MAP, LASKUN_TILA_MAP,
    LASKUTYYPPI_MAP, LEASE_AREA_TYPE_MAP, MANAGEMENT_MAP, SAAMISLAJI_MAP, TILA_MAP, VUOKRAKAUSI_MAP, VUOKRALAJI_MAP)
from .utils import (
    asiakas_cache, expand_lease_identifier, expanded_id_to_query, expanded_id_to_query_alku, get_or_create_contact,
    get_real_property_identifier, get_unknown_contact, rows_to_dict_list)


class LeaseImporter(BaseImporter):
    type_name = 'lease'

    def __init__(self, stdout=None, stderr=None):
        connection = cx_Oracle.connect(user='mvj', password='mvjpass', dsn='localhost:1521/ORCLPDB1', encoding="UTF-8",
                                       nencoding="UTF-8")

        self.cursor = connection.cursor()
        self.stdout = stdout
        self.stderr = stderr
        self.related_leases = []
        self.lease_ids = None
        self.offset = 0

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument('--lease-ids', dest='lease_ids', type=str, required=False,
                            help='comma separated list of lease ids to import (default: all)')
        parser.add_argument('--offset', dest='offset', type=int, required=False,
                            help='lease start offset')

    def read_options(self, options):
        if options['lease_ids']:
            self.lease_ids = []
            for lease_id in options['lease_ids'].split(','):
                lease_id = lease_id.strip().upper()
                id_match = re.match(r'(?P<lease_type>\w\d)(?P<municipality>\d)(?P<district>\d{2})-(?P<sequence>\d+)$',
                                    lease_id)

                if not id_match:
                    raise RuntimeError('identifier "{}" doesn\'t match the identifier format'.format(lease_id))

                self.lease_ids.append(lease_id)

        if not self.lease_ids and options['offset']:
            self.offset = options['offset']

    def execute(self):
        from auditlog.registry import auditlog

        # Unregister all models from auditlog when importing
        for model in list(auditlog._registry.keys()):
            auditlog.unregister(model)

        self.import_leases()
        self.update_related_leases()

    def get_or_create_default_lessor(self):
        (contact, contact_created) = Contact.objects.get_or_create(
            is_lessor=True,
            name='Maaomaisuuden kehittäminen ja tontit',
            defaults={
                'type': ContactType.UNIT,
                'address': 'PL2214',
                'postal_code': '00099',
                'city': 'Helsingin kaupunki',
                'business_id': '',
                'sap_sales_office': 2826,
            })

        return contact

    def import_leases(self):  # noqa: C901 'Command.handle' is too complex
        cursor = self.cursor

        default_lessor = self.get_or_create_default_lessor()

        if self.lease_ids is None:
            query = """
                SELECT * FROM (
                    SELECT ALKUOSA, JUOKSU, ROW_NUMBER() OVER (ORDER BY ALKUPVM) rn
                    FROM VUOKRAUS
                    WHERE TILA <> 'S'
                    ORDER BY ALKUPVM
                ) t
                WHERE rn >= {}
                """.format(self.offset)

            cursor.execute(query)
            self.lease_ids = ['{}-{}'.format(row[0], row[1]) for row in cursor]

        lease_id_count = len(self.lease_ids)
        self.stdout.write('{} lease ids'.format(lease_id_count))

        # LEASE_TYPE_MAP = {lt.identifier: lt.id for lt in LeaseType.objects.all()}
        intended_use_map = {intended_use.name: intended_use.id for intended_use in IntendedUse.objects.all()}

        count = 0
        if self.offset:
            count = self.offset - 1
            lease_id_count += self.offset

        for lease_id in self.lease_ids:
            if not lease_id:
                continue

            count += 1
            self.stdout.write('\n{} ({}/{})'.format(lease_id, count, lease_id_count))

            id_parts = expand_lease_identifier(lease_id)

            # self.stdout.write(expanded_id_to_query(id_parts))

            asiakas_num_to_tenant = {}

            query = """
                SELECT v.*, k.NIMI AS KTARK_NIMI
                FROM VUOKRAUS v
                LEFT JOIN KTARK_KOODI k ON v.KTARK_KOODI = k.KTARK_KOODI""" + expanded_id_to_query(id_parts)

            cursor.execute(query)

            vuokraus_rows = rows_to_dict_list(cursor)

            for lease_row in vuokraus_rows:
                if id_parts['KUNTA'] == 0:
                    self.stdout.write(' Municipality is 0! Skipping.')
                    continue

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
                lease.lessor = default_lessor

                if id_parts['TARKOITUS'] == 'T3':
                    lease.is_subject_to_vat = True

                notes = []

                query = """
                    SELECT TEKSTI
                    FROM TUNNUS_OPASTE""" + expanded_id_to_query(id_parts)

                cursor.execute(query)
                for row in cursor:
                    if not row[0]:
                        continue

                    notes.append(row[0])

                if lease_row['HAKEMUS_SISALTO']:
                    notes.append(lease_row['HAKEMUS_SISALTO'])
                if lease_row['SIIRTO_TXT']:
                    notes.append(lease_row['SIIRTO_TXT'])

                lease.note = '\n'.join(notes)

                if lease_row['SIIRTO_OIKEUS'] == 'K':
                    lease.transferable = True
                elif lease_row['SIIRTO_OIKEUS'] == 'E':
                    lease.transferable = False

                lease.is_invoicing_enabled = True if lease_row['LASKUTUS'] == 'K' else False

                lease.save()

                self.stdout.write('Lease id {}'.format(lease.id))

                self.stdout.write("Related to lease:")
                if lease_row['LIITTYY_ALKUOSA'] != lease_row['ALKUOSA'] or \
                        lease_row['LIITTYY_JUOKSU'] != lease_row['JUOKSU']:
                    related_identifier = "{}-{}".format(lease_row['LIITTYY_ALKUOSA'], lease_row['LIITTYY_JUOKSU'])

                    self.stdout.write(" {}".format(related_identifier))

                    related_type = None
                    if lease.state == LeaseState.TRANSFER:
                        related_type = LeaseRelationType.TRANSFER

                    self.related_leases.append({
                        'from_lease': related_identifier,
                        'to_lease': lease,
                        'type': related_type,
                    })

                self.stdout.write(" {} relations".format(len(self.related_leases)))

                self.stdout.write("Vuokralaiset:")
                query = """
                    SELECT ar.*, a.*
                    FROM ASROOLI ar
                    LEFT JOIN ASIAKAS a ON ar.ASIAKAS = a.ASIAKAS""" + expanded_id_to_query_alku(id_parts)

                cursor.execute(query)
                asrooli_rows = rows_to_dict_list(cursor)

                for role_row in [row for row in asrooli_rows if row['ROOLI'] == 'V']:
                    self.stdout.write(" ASIAKAS V #{}".format(role_row['ASIAKAS']))
                    contact = get_or_create_contact(role_row)
                    self.stdout.write('  Contact {}'.format(contact))

                    start_date = role_row['ALKAEN']
                    if 2100 < start_date.year < 2200:
                        start_date = start_date.replace(year=start_date.year - 100)

                    if 3000 < start_date.year < 3100:
                        start_date = start_date.replace(year=start_date.year - 1000)

                    try:
                        tenant = lease.tenants.get(tenantcontact__contact=contact,
                                                   tenantcontact__type=TenantContactType.TENANT,
                                                   tenantcontact__start_date=start_date,
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
                        start_date=start_date,
                        end_date=role_row['SAAKKA']
                    )

                    asiakas_num_to_tenant[role_row['ASIAKAS']] = tenant

                for role_row in [row for row in asrooli_rows if row['ROOLI'] in ('L', 'Y')]:
                    self.stdout.write(" ASIAKAS {} #{}".format(role_row['ROOLI'], role_row['ASIAKAS']))
                    contact = get_or_create_contact(role_row)
                    self.stdout.write('  Contact {}'.format(contact))

                    start_date = role_row['ALKAEN']
                    if 2100 < start_date.year < 2200:
                        start_date = start_date.replace(year=start_date.year - 100)

                    if 3000 < start_date.year < 3100:
                        start_date = start_date.replace(year=start_date.year - 1000)

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
                            start_date=start_date,
                            end_date=role_row['SAAKKA']
                        )

                        asiakas_num_to_tenant[role_row['ASIAKAS']] = this_tenant

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
                    try:
                        rent.y_value_start = datetime.date(year=lease_row['Y_VVVV'], month=lease_row['Y_KK'], day=1)
                    except ValueError as e:
                        self.stdout.write(" Invalid month/year: Exception " + str(e))

                if index_type == IndexType.TYPE_1:
                    rent.elementary_index = 50620

                if index_type == IndexType.TYPE_2:
                    rent.elementary_index = 4661

                if index_type == IndexType.TYPE_3:
                    rent.elementary_index = 418
                    rent.index_rounding = 10

                if index_type == IndexType.TYPE_4:
                    rent.elementary_index = 418
                    rent.index_rounding = 20

                if index_type == IndexType.TYPE_5:
                    rent.elementary_index = 392

                if index_type == IndexType.TYPE_6:
                    rent.elementary_index = 100
                    rent.index_rounding = 10

                rent.equalization_start_date = lease_row['TASAUS_ALKUPVM']
                rent.equalization_end_date = lease_row['TASAUS_LOPPUPVM']
                rent.save()

                self.stdout.write(" Type: {} Index: {}".format(rent_type, index_type))

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
                        FROM VUOKRAUKSEN_ERAPAIVA""" + expanded_id_to_query_alku(id_parts)

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
                    self.stdout.write("Kiinteä alkuvuosivuokra {}".format(lease_row['KIINTEA_ALKUVUOSIVUOKRAN_MAARA']))

                    (initial_rent, initial_rent_created) = FixedInitialYearRent.objects.get_or_create(
                        rent=rent,
                        amount=lease_row['KIINTEA_ALKUVUOSIVUOKRAN_MAARA'],
                        start_date=lease_row['ALKUPVM'] if lease_row['ALKUPVM'] else None,
                        end_date=lease_row['KIINTEA_ALKUVUOSIVUOKRAN_LOPPU'])

                self.stdout.write("Sopimusvuokrat:")

                query = """
                    SELECT sv.*, kt.NIMI as kt_nimi
                    FROM SOPIMUSVUOKRA sv
                    LEFT JOIN KAYTTOTARKOITUS kt ON sv.KAYTTOTARKOITUS = kt.KAYTTOTARKOITUS""" + \
                        expanded_id_to_query_alku(id_parts)

                cursor.execute(query)
                sopimusvuokra_rows = rows_to_dict_list(cursor)

                self.stdout.write(" {} rows".format(len(sopimusvuokra_rows)))

                for rent_row in sopimusvuokra_rows:
                    contract_rent_amount = None
                    contract_rent_period = None
                    if rent_row['SOPIMUSVUOKRA_VUOSI'] is not None:
                        contract_rent_amount = rent_row['SOPIMUSVUOKRA_VUOSI']
                        contract_rent_period = PeriodType.PER_YEAR

                    if rent_row['SOPIMUSVUOKRA_KK'] is not None:
                        contract_rent_amount = rent_row['SOPIMUSVUOKRA_KK']
                        contract_rent_period = PeriodType.PER_MONTH

                    if contract_rent_amount is None:
                        continue

                    try:
                        contract_rent_intended_use = RentIntendedUse.objects.get(pk=rent_row['KAYTTOTARKOITUS'])
                    except RentIntendedUse.DoesNotExist:
                        (contract_rent_intended_use, _) = RentIntendedUse.objects.get_or_create(
                            id=rent_row['KAYTTOTARKOITUS'], name=rent_row['KT_NIMI'])

                    (contract_rent, contract_rent_created) = ContractRent.objects.get_or_create(
                        rent=rent, period=contract_rent_period, intended_use=contract_rent_intended_use,
                        start_date=rent_row['ALKUPVM'].date() if rent_row['ALKUPVM'] else None,
                        end_date=rent_row['LOPPUPVM'].date() if rent_row['LOPPUPVM'] else None,
                        base_year_rent=rent_row['UUSI_PERUSVUOKRA'],
                        defaults={
                            'amount': contract_rent_amount,
                            'base_amount': rent_row['PERUSVUOKRA'] if rent_row['PERUSVUOKRA'] else contract_rent_amount,
                            'base_amount_period': contract_rent_period,
                        }
                    )

                    # TODO: No intended use for initial year rent in the old system
                    if initial_rent and not initial_rent.intended_use_id:
                        initial_rent.intended_use = contract_rent_intended_use
                        initial_rent.save()

                if rent.type == RentType.ONE_TIME:
                    # Calculate one time rent from sent invoices
                    self.stdout.write("Kertakaikkinen vuokra:")
                    query = """
                        SELECT *
                        FROM R_LASKU""" + expanded_id_to_query(id_parts)

                    cursor.execute(query)
                    lasku_rows = rows_to_dict_list(cursor)

                    one_time_amount = Decimal(0)
                    for lasku_row in lasku_rows:
                        one_time_amount += Decimal(lasku_row['LASKUTETTU_MAARA'])

                    if one_time_amount:
                        one_time_amount = one_time_amount.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
                        self.stdout.write(" {}e".format(one_time_amount))

                        rent.amount = one_time_amount
                        rent.save()

                self.stdout.write("Tarkistettu vuokra:")

                query = """
                    SELECT *
                    FROM TARKISTETTU_VUOKRA""" + expanded_id_to_query_alku(id_parts)

                cursor.execute(query)
                tarkistettu_vuokra_rows = rows_to_dict_list(cursor)

                self.stdout.write(" {} rows".format(len(tarkistettu_vuokra_rows)))

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
                    FROM VUOSIVUOKRA""" + expanded_id_to_query_alku(id_parts)

                cursor.execute(query)
                vuosivuokra_rows = rows_to_dict_list(cursor)

                self.stdout.write(" {} rows".format(len(vuosivuokra_rows)))

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
                    FROM ALENNUS""" + expanded_id_to_query_alku(id_parts)

                cursor.execute(query)
                alennus_rows = rows_to_dict_list(cursor)

                self.stdout.write(" {} rows".format(len(alennus_rows)))

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

                self.stdout.write("Tasattu vuokra:")

                query = """
                    SELECT *
                    FROM TASATTUVUOKRA""" + expanded_id_to_query_alku(id_parts)

                cursor.execute(query)
                tasattuvuokra_rows = rows_to_dict_list(cursor)

                self.stdout.write(" {} rows".format(len(tasattuvuokra_rows)))

                for rent_row in tasattuvuokra_rows:
                    (equalized_rent, equalized_rent_created) = EqualizedRent.objects.get_or_create(
                        rent=rent,
                        start_date=rent_row['ALKUPVM'].date() if rent_row['ALKUPVM'] else None,
                        end_date=rent_row['LOPPUPVM'].date() if rent_row['LOPPUPVM'] else None,
                        payable_amount=rent_row['PERITTAVAVUOKRA'],
                        equalized_payable_amount=rent_row['TASATTU_PERITTAVAVUOKRA'],
                        equalization_factor=rent_row['TASAUSKERROIN'],
                    )

                self.stdout.write("Lasku:")

                query = """
                    SELECT l.*, a.*, l.ASIAKAS AS LASKU_ASIAKAS
                    FROM R_LASKU l
                    LEFT JOIN ASIAKAS a ON l.ASIAKAS = a.ASIAKAS""" + expanded_id_to_query(id_parts)

                cursor.execute(query)
                lasku_rows = rows_to_dict_list(cursor)

                self.stdout.write(" {} rows".format(len(lasku_rows)))

                for invoice_row in lasku_rows:
                    if invoice_row['ASIAKAS']:
                        contact = get_or_create_contact(invoice_row)
                    else:
                        self.stdout.write('ASIAKAS #{} in Invoice #{} missing. Using unkown_contact.'.format(
                            invoice_row['LASKU_ASIAKAS'], invoice_row['LASKU']
                        ))
                        contact = get_unknown_contact()

                    receivable_type_id = SAAMISLAJI_MAP[invoice_row['SAAMISLAJI']]
                    invoice_state = LASKUN_TILA_MAP[invoice_row['LASKUN_TILA']]
                    invoice_type = LASKUTYYPPI_MAP[invoice_row['LASKUTYYPPI']]

                    period_start_date = invoice_row['LASKUTUSKAUSI_ALKAA'].date() if invoice_row[
                        'LASKUTUSKAUSI_ALKAA'] else None
                    period_end_date = invoice_row['LASKUTUSKAUSI_PAATTYY'].date() if invoice_row[
                        'LASKUTUSKAUSI_PAATTYY'] else None

                    # period_start_date = invoice_row['LASKUTUSKAUSI_ALKAA'].date() if invoice_row[
                    #     'LASKUTUSKAUSI_ALKAA'] else lease.start_date
                    # period_end_date = invoice_row['LASKUTUSKAUSI_PAATTYY'].date() if invoice_row[
                    #     'LASKUTUSKAUSI_PAATTYY'] else lease.end_date
                    # if not period_end_date:
                    #     period_end_date = period_start_date

                    sent_to_sap_at = make_aware(invoice_row['SAP_SIIRTOPVM']) if invoice_row['SAP_SIIRTOPVM'] else None

                    (invoice, invoice_created) = Invoice.objects.get_or_create(
                        lease=lease,
                        number=invoice_row['LASKU'],
                        recipient=contact,
                        due_date=invoice_row['ERAPVM'],
                        state=invoice_state,
                        billing_period_start_date=period_start_date,
                        billing_period_end_date=period_end_date,
                        invoicing_date=invoice_row['LASKUTUSPVM'],
                        postpone_date=invoice_row['LYKKAYSPVM'],
                        total_amount=invoice_row['LASKUN_PAAOMA'],
                        billed_amount=invoice_row['LASKUTETTU_MAARA'],
                        outstanding_amount=invoice_row['MAKSAMATON_MAARA'],
                        payment_notification_date=invoice_row['MAKSUKEHOITUSPVM1'],
                        collection_charge=invoice_row['PERINTAKULU1'],
                        payment_notification_catalog_date=invoice_row['MAKSUKEHLUETAJOPVM1'],
                        delivery_method=InvoiceDeliveryMethod.MAIL,
                        type=invoice_type,
                        notes='',  # TODO
                        generated=True,  # TODO
                        sent_to_sap_at=sent_to_sap_at,
                    )

                    (invoice_row_instance, invoice_row_created) = InvoiceRow.objects.get_or_create(
                        invoice=invoice,
                        tenant=asiakas_num_to_tenant[
                            invoice_row['ASIAKAS']] if invoice_row['ASIAKAS'] in asiakas_num_to_tenant else None,
                        receivable_type_id=receivable_type_id,
                        billing_period_start_date=period_start_date,
                        billing_period_end_date=period_end_date,
                        amount=invoice_row['LASKUN_OSUUS']
                    )

                    # if period_end_date.year != period_start_date.year:
                    #     invoice.billing_period_end_date = datetime.date(
                    #         year=period_start_date.year, month=period_end_date.month, day=period_end_date.day)
                    #     invoice.save()

                    query = """
                        SELECT *
                        FROM R_MAKSU
                        WHERE LASKU = {}
                        """.format(invoice_row['LASKU'])

                    cursor.execute(query)
                    maksu_rows = rows_to_dict_list(cursor)

                    for payment_row in maksu_rows:
                        (invoice_payment, invoice_payment_created) = InvoicePayment.objects.get_or_create(
                            invoice=invoice,
                            paid_amount=payment_row['MAARA'],
                            paid_date=payment_row['MAKSUPVM'].date() if payment_row['MAKSUPVM'] else None,
                        )

                self.stdout.write('Vuokra-alue:')

                query = """
                    SELECT h.*, k.KIINTEISTOTYYPPI, k.PINTA_ALA_M2, k.OSOITE
                    FROM HALLINTA h
                    LEFT JOIN VUOKRAKOHDE k ON k.KOHDE = h.KOHDE""" + expanded_id_to_query_alku(id_parts)

                cursor.execute(query)
                kohde_rows = rows_to_dict_list(cursor)

                self.stdout.write(" {} rows".format(len(kohde_rows)))

                for lease_area_row in kohde_rows:
                    identifier = get_real_property_identifier(lease_area_row)

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
                            is_primary=True
                        )

                    query = """
                        SELECT *
                        FROM OSOITE
                        WHERE KOHDE = '{}'
                        """.format(lease_area_row['KOHDE'])

                    cursor.execute(query)
                    address_rows = rows_to_dict_list(cursor)

                    for address_row in address_rows:
                        if address_row['OSOITE'] == lease_area_row['OSOITE']:
                            continue

                        (lease_area_address, lease_area_address_created) = LeaseAreaAddress.objects.get_or_create(
                            lease_area=lease_area,
                            address=address_row['OSOITE'],
                            is_primary=False
                        )

                self.stdout.write('Päätökset:')

                query = """
                    SELECT *
                    FROM PAATOS""" + expanded_id_to_query_alku(id_parts)

                cursor.execute(query)
                paatos_rows = rows_to_dict_list(cursor)

                self.stdout.write(" {} rows".format(len(paatos_rows)))

                lease_decisions = {}

                for decision_row in paatos_rows:
                    decision_maker_id = None
                    try:
                        decision_maker_id = DECISION_MAKER_MAP[decision_row['PAATTAJA']]
                    except KeyError:
                        self.stdout.write(' Decision maker "{}" not found in DECISION_MAKER_MAP!'.format(
                            decision_row['PAATTAJA']))

                    (decision, decision_created) = Decision.objects.get_or_create(
                        lease=lease,
                        reference_number=None,
                        decision_maker_id=decision_maker_id,
                        decision_date=decision_row['PAATOSPVM'].date() if decision_row['PAATOSPVM'] else None,
                        section=decision_row['PYKALA'],
                        type_id=decision_row['PAATOSTYYPPI'],
                        description=decision_row['PAATOSTXT'],
                    )

                    lease_decisions[decision_row['PAATOS']] = decision

                    query = """
                        SELECT *
                        FROM VUOKRAUKSEN_EHTO
                        WHERE PAATOS = '{}'
                        """.format(decision_row['PAATOS'])

                    cursor.execute(query)
                    ehto_rows = rows_to_dict_list(cursor)

                    for condition_row in ehto_rows:
                        (condition, condition_created) = Condition.objects.get_or_create(
                            decision=decision,
                            type_id=int(condition_row['EHTOTYYPPI']),
                            supervision_date=condition_row['VALVONTAPVM'],
                            supervised_date=condition_row['VALVOTTUPVM'],
                            description=condition_row['EHTOTXT'],
                        )

                self.stdout.write('Vuokrauksen ehdot:')

                query = """
                    SELECT *
                    FROM VUOKRAUKSEN_EHTO
                    WHERE PAATOS = '0'""" + expanded_id_to_query_alku(id_parts, where=False)

                cursor.execute(query)
                ehto_rows = rows_to_dict_list(cursor)

                self.stdout.write(" {} rows".format(len(ehto_rows)))

                if len(ehto_rows):
                    (bogus_decision, decision_created) = Decision.objects.get_or_create(
                        lease=lease,
                        reference_number=None,
                        decision_maker_id=None,
                        decision_date=None,
                        section=None,
                        type_id=None,
                        description='Vuokrauksen ehdot',
                    )

                    for condition_row in ehto_rows:
                        (condition, condition_created) = Condition.objects.get_or_create(
                            decision=bogus_decision,
                            type_id=int(condition_row['EHTOTYYPPI']),
                            supervision_date=condition_row['VALVONTAPVM'],
                            supervised_date=condition_row['VALVOTTUPVM'],
                            description=condition_row['EHTOTXT'],
                        )

                self.stdout.write('Sopimukset:')

                query = """
                    SELECT s.*, sl.KOMMENTTI AS LAITOSTUNNUS_KOMMENTTI
                    FROM SOPIMUS s
                    LEFT JOIN MVJ.SOPIMUS_LAITOSTUNNUS sl ON s.SOPIMUS = sl.SOPIMUS""" + expanded_id_to_query_alku(
                        id_parts)

                cursor.execute(query)
                sopimus_rows = rows_to_dict_list(cursor)

                self.stdout.write(" {} rows".format(len(sopimus_rows)))

                for contract_row in sopimus_rows:
                    # TODO: Other contract numbers
                    if not re.fullmatch(r'\d+', contract_row['SOPIMUS']):
                        continue

                    note = contract_row['KOMMENTTI']
                    if contract_row['LAITOSTUNNUS_KOMMENTTI'] and contract_row['KOMMENTTI'] != contract_row[
                            'LAITOSTUNNUS_KOMMENTTI']:
                        if note:
                            note += ' ' + contract_row['LAITOSTUNNUS_KOMMENTTI']
                        else:
                            note = contract_row['LAITOSTUNNUS_KOMMENTTI']

                    (contract, contract_created) = Contract.objects.get_or_create(
                        lease=lease,
                        type_id=1,  # Vuokrasopimus
                        contract_number=contract_row['SOPIMUS'],
                        signing_date=contract_row['ALLEKIRJPVM'].date() if contract_row['ALLEKIRJPVM'] else None,
                        signing_note=note,
                        is_readjustment_decision=bool(contract_row['JARJESTELYPAATOS']),
                        institution_identifier=contract_row['LAITOSTUNNUS'],
                    )
                    if (contract_row['VUOKRAKIINNITYSPYKALA'] or contract_row['VUOKRAKIINNITYSPVM'] or
                            contract_row['VUOKRAKIINNITYSLOPPUPVM'] or contract_row['KOMMENTTI']):
                        Collateral.objects.get_or_create(
                            contract=contract,
                            type_id=2,  # Rahavakuus
                            number=contract_row['VUOKRAKIINNITYSPYKALA'],
                            start_date=contract_row['VUOKRAKIINNITYSPVM'].date() if
                            contract_row['VUOKRAKIINNITYSPVM'] else None,
                            end_date=contract_row['VUOKRAKIINNITYSLOPPUPVM'].date() if
                            contract_row['VUOKRAKIINNITYSLOPPUPVM'] else None,
                            note=None
                        )

                    Collateral.objects.get_or_create(
                        contract=contract,
                        type_id=1,  # Panttikirja
                        number=contract_row['PYSYVYYSKIINNITYSPYKALA'],
                        start_date=contract_row['PYSYVYYSKIINNITYSPVM'].date() if contract_row[
                            'PYSYVYYSKIINNITYSPVM'] else None,
                        note=None
                    )

                    self.stdout.write('Sopimuksen muutokset:')

                    query = """
                        SELECT *
                        FROM SOPIMUS_MUUTOS
                        WHERE SOPIMUS = '{}'
                        """.format(contract_row['SOPIMUS'])

                    cursor.execute(query)
                    sopimus_muutos_rows = rows_to_dict_list(cursor)

                    self.stdout.write(" {} rows".format(len(sopimus_muutos_rows)))

                    for contract_change_row in sopimus_muutos_rows:
                        decision = None
                        try:
                            decision = lease_decisions[contract_change_row['PAATOS']]
                        except KeyError:
                            self.stdout.write(' Decision #{} NOT FOUND'.format(contract_change_row['PAATOS']))

                        (contract_change, contract_change_created) = ContractChange.objects.get_or_create(
                            contract=contract,
                            signing_date=contract_change_row['ALLEKIRJPVM'].date() if contract_change_row[
                                'ALLEKIRJPVM'] else None,
                            sign_by_date=contract_change_row['ALLEKIRJ_MENNESSAPVM'].date() if contract_change_row[
                                'ALLEKIRJ_MENNESSAPVM'] else None,
                            first_call_sent=contract_change_row['KUTSUN_LAHETYSPVM'].date() if contract_change_row[
                                'KUTSUN_LAHETYSPVM'] else None,
                            second_call_sent=contract_change_row['KUTSUN_LAHETYSPVM2'].date() if contract_change_row[
                                'KUTSUN_LAHETYSPVM2'] else None,
                            third_call_sent=contract_change_row['KUTSUN_LAHETYSPVM3'].date() if contract_change_row[
                                'KUTSUN_LAHETYSPVM3'] else None,
                            description=contract_change_row['KOMMENTTITXT'],
                            decision=decision,
                        )

                self.stdout.write('Tarkastukset:')

                query = """
                    SELECT *
                    FROM TARKASTUS""" + expanded_id_to_query_alku(id_parts)

                cursor.execute(query)
                tarkastus_rows = rows_to_dict_list(cursor)

                self.stdout.write(" {} rows".format(len(tarkastus_rows)))

                for inspection_row in tarkastus_rows:
                    self.stdout.write(' Inspection #{}'.format(inspection_row['TARKASTUS']))

                    descriptions = []

                    if inspection_row['KOMMENTTITXT']:
                        descriptions.append(inspection_row['KOMMENTTITXT'])

                    if inspection_row['TOIMENPIDE_EHDOTUS']:
                        descriptions.append('\nToimenpide-ehdotus:')
                        descriptions.append(' ' + inspection_row['TOIMENPIDE_EHDOTUS'])
                        descriptions.append('\n')

                    query = """
                        SELECT *
                        FROM TARKASTUS_KEHOTUS
                        WHERE TARKASTUS = '{}'
                        ORDER BY VALVONTAPVM
                        """.format(inspection_row['TARKASTUS'])

                    cursor.execute(query)
                    tarkastus_kehotus_rows = rows_to_dict_list(cursor)

                    self.stdout.write(' {} requests'.format(len(tarkastus_kehotus_rows)))

                    if tarkastus_kehotus_rows:
                        descriptions.append('\nKehotukset:')

                    for inspection_request_row in tarkastus_kehotus_rows:
                        if not inspection_request_row['KEHOTUSTXT']:
                            continue

                        descriptions.append(' Valvontapvm: {}\n Valvottu pvm: {}\n {}\n'.format(
                            inspection_request_row['VALVONTAPVM'].date()
                            if inspection_request_row['VALVONTAPVM'] else '',
                            inspection_request_row['VALVOTTUPVM'].date()
                            if inspection_request_row['VALVOTTUPVM'] else '',
                            inspection_request_row['KEHOTUSTXT'],
                        ))

                    query = """
                        SELECT *
                        FROM TARKASTUS_KAYNTI
                        WHERE TARKASTUS = '{}'
                        ORDER BY TARKASTUSPVM
                        """.format(inspection_row['TARKASTUS'])

                    cursor.execute(query)
                    tarkastus_kaynti_rows = rows_to_dict_list(cursor)

                    self.stdout.write('  {} visits'.format(len(tarkastus_kaynti_rows)))

                    if tarkastus_kaynti_rows:
                        descriptions.append('\nKäynnit:')

                    for inspection_visit_row in tarkastus_kaynti_rows:
                        if not inspection_visit_row['TARKASTUSKERTOMUSTXT']:
                            continue

                        descriptions.append(' Tarkastus pvm: {}\n Tarkastaja: {}\n {}\n'.format(
                            inspection_visit_row['TARKASTUSPVM'].date() if inspection_visit_row['TARKASTUSPVM'] else '',
                            inspection_visit_row['TARKASTAJA'],
                            inspection_visit_row['TARKASTUSKERTOMUSTXT'],
                        ))

                    query = """
                        SELECT *
                        FROM TARKASTUS_VASTINE
                        WHERE TARKASTUS = '{}'
                        ORDER BY SAAPUMISPVM
                        """.format(inspection_row['TARKASTUS'])

                    cursor.execute(query)
                    tarkastus_vastine_rows = rows_to_dict_list(cursor)

                    self.stdout.write('  {} replies'.format(len(tarkastus_vastine_rows)))

                    if tarkastus_vastine_rows:
                        descriptions.append('\nVastineet:')

                    for inspection_reply_row in tarkastus_vastine_rows:
                        if not inspection_reply_row['VASTINETXT']:
                            continue

                        descriptions.append(' Saapumispvm: {}\n {}\n'.format(
                            inspection_reply_row['SAAPUMISPVM'].date() if inspection_reply_row['SAAPUMISPVM'] else '',
                            inspection_reply_row['VASTINETXT'],
                        ))

                    (inspection, inspection_created) = Inspection.objects.get_or_create(
                        lease=lease,
                        inspector=inspection_row['TARKASTAJA'],
                        supervision_date=None,
                        supervised_date=None,
                        description='\n'.join(descriptions),
                    )

    def update_related_leases(self):
        if not self.related_leases:
            return

        self.stdout.write('Updating related leases:')

        for related_lease_data in self.related_leases:
            self.stdout.write(' {} -> {}'.format(related_lease_data['from_lease'],
                                                 related_lease_data['to_lease']))

            try:
                from_lease = Lease.objects.get_by_identifier(related_lease_data['from_lease'])
                (related_lease, related_lease_created) = RelatedLease.objects.get_or_create(
                    from_lease=from_lease,
                    to_lease=related_lease_data['to_lease'],
                    type=related_lease_data['type']
                )
            except Lease.DoesNotExist:
                self.stdout.write('  Lease {} does not exist!'.format(related_lease_data['from_lease']))

        self.stdout.write(' {} relations'.format(len(self.related_leases)))
