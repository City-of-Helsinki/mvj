import datetime
import re

from django.core.exceptions import ObjectDoesNotExist

import cx_Oracle
from leasing.enums import (
    ContactType, DueDatesPosition, DueDatesType, IndexType, InvoiceDeliveryMethod, LeaseRelationType, LeaseState,
    LocationType, PeriodType, RentAdjustmentAmountType, TenantContactType)
from leasing.models import (
    Contact, Contract, ContractChange, ContractRent, Decision, District, FixedInitialYearRent, IndexAdjustedRent,
    IntendedUse, Invoice, Lease, LeaseArea, LeaseIdentifier, LeaseType, MortgageDocument, Municipality, PayableRent,
    RelatedLease, Rent, RentAdjustment, RentIntendedUse, Tenant, TenantContact)
from leasing.models.invoice import InvoicePayment, InvoiceRow
from leasing.models.land_area import LeaseAreaAddress
from leasing.models.rent import FIXED_DUE_DATES, RentDueDate
from leasing.models.utils import DayMonth

from .base import BaseImporter
from .mappings import (
    ALENNUS_KOROTUS_MAP, ASIAKASTYYPPI_MAP, DECISION_MAKER_MAP, FINANCING_MAP, HITAS_MAP, IRTISANOMISAIKA_MAP,
    LASKUN_TILA_MAP, LASKUTYYPPI_MAP, LEASE_AREA_TYPE_MAP, MANAGEMENT_MAP, SAAMISLAJI_MAP, TILA_MAP, VUOKRAKAUSI_MAP,
    VUOKRALAJI_MAP)
from .utils import (
    asiakas_cache, expand_lease_identifier, expanded_id_to_query, expanded_id_to_query_alku, get_or_create_contact,
    get_real_property_identifier, get_unknown_contact, rows_to_dict_list)


class LeaseImporter(BaseImporter):
    type_name = 'lease'

    def __init__(self, stdout=None):
        connection = cx_Oracle.connect(user='mvj', password='mvjpass', dsn='localhost:1521/ORCLPDB1', encoding="UTF-8",
                                       nencoding="UTF-8")

        self.cursor = connection.cursor()
        self.stdout = stdout
        self.related_leases = []
        self.lease_ids = None
        self.invoice_numbers = {}
        self.credit_notes = []

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument('--lease-ids', dest='lease_ids', type=str, required=False,
                            help='comma separated list of lease ids to import (default: all)')

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

    def execute(self):
        self.import_leases()
        self.update_related_leases()
        self.update_credit_notes()

    def import_leases(self):  # noqa: C901 'Command.handle' is too complex
        cursor = self.cursor

        if self.lease_ids is None:
            query = """
                SELECT ALKUOSA, JUOKSU
                FROM VUOKRAUS
                WHERE ALKUPVM >= TO_DATE('01/01/2016', 'DD/MM/YYYY')
                  AND ALKUPVM < TO_DATE('01/01/2017', 'DD/MM/YYYY')
                ORDER BY ALKUPVM
                """
            cursor.execute(query)
            self.lease_ids = ['{}-{}'.format(row[0], row[1]) for row in cursor]

        lease_id_count = len(self.lease_ids)
        self.stdout.write('{} lease ids'.format(lease_id_count))

        # LEASE_TYPE_MAP = {lt.identifier: lt.id for lt in LeaseType.objects.all()}
        intended_use_map = {intended_use.name: intended_use.id for intended_use in IntendedUse.objects.all()}

        count = 0
        for lease_id in self.lease_ids:
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
                lease.note = lease_row['SIIRTO_TXT']

                if lease_row['SIIRTO_OIKEUS'] == 'K':
                    lease.transferable = True
                elif lease_row['SIIRTO_OIKEUS'] == 'E':
                    lease.transferable = False

                lease.is_invoicing_enabled = True if lease_row['LASKUTUS'] == 'K' else False

                lease.save()

                self.stdout.write("Related to lease:")
                if lease_row['LIITTYY_ALKUOSA'] != lease_row['ALKUOSA'] or \
                        lease_row['LIITTYY_JUOKSU'] != lease_row['JUOKSU']:
                    related_identifier = "{}-{}".format(lease_row['LIITTYY_ALKUOSA'], lease_row['LIITTYY_JUOKSU'])

                    self.stdout.write(" {}".format(related_identifier))

                    related_type = None
                    if lease.state == LeaseState.TRANSFERRED:
                        related_type = LeaseRelationType.TRANSFER

                    self.related_leases.append({
                        'from_lease': related_identifier,
                        'to_lease': lease,
                        'type': related_type,
                    })

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
                    contact = get_or_create_contact(role_row)
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
                    contact = get_or_create_contact(role_row)
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

                query = """
                    SELECT sv.*, kt.NIMI as kt_nimi
                    FROM SOPIMUSVUOKRA sv
                    LEFT JOIN KAYTTOTARKOITUS kt ON sv.KAYTTOTARKOITUS = kt.KAYTTOTARKOITUS
                    WHERE 1 = 1
                    """ + expanded_id_to_query_alku(id_parts)

                cursor.execute(query)
                sopimusvuokra_rows = rows_to_dict_list(cursor)

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
                    SELECT l.*, a.*, l.ASIAKAS AS LASKU_ASIAKAS, hl.lasku AS CREDITED_INVOICE
                    FROM R_LASKU l
                    LEFT JOIN R_LASKU_HYVITYSLASKU hl ON hl.HYVITYSLASKU = l.LASKU
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
                        contact = get_unknown_contact()

                    receivable_type_id = SAAMISLAJI_MAP[invoice_row['SAAMISLAJI']]
                    invoice_state = LASKUN_TILA_MAP[invoice_row['LASKUN_TILA']]
                    invoice_type = LASKUTYYPPI_MAP[invoice_row['LASKUTYYPPI']]

                    period_start_date = invoice_row['LASKUTUSKAUSI_ALKAA'].date() if invoice_row[
                        'LASKUTUSKAUSI_ALKAA'] else lease.start_date
                    period_end_date = invoice_row['LASKUTUSKAUSI_PAATTYY'].date() if invoice_row[
                        'LASKUTUSKAUSI_PAATTYY'] else lease.end_date

                    if not period_end_date:
                        period_end_date = period_start_date

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

                    self.invoice_numbers[invoice_row['LASKU']] = invoice.id
                    if invoice_row['CREDITED_INVOICE']:
                        credit_note_datum = {
                            "credit_note": invoice,
                            "credited_invoice_number": invoice_row['CREDITED_INVOICE'],
                            "credited_invoice_id": self.invoice_numbers[invoice_row['CREDITED_INVOICE']] if invoice_row[
                                'CREDITED_INVOICE'] in self.invoice_numbers else None,
                        }

                        self.credit_notes.append(credit_note_datum)

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
                    SELECT *
                    FROM HALLINTA h
                    LEFT JOIN VUOKRAKOHDE k ON k.KOHDE = h.KOHDE
                    WHERE 1 = 1
                    """ + expanded_id_to_query_alku(id_parts)

                cursor.execute(query)
                kohde_rows = rows_to_dict_list(cursor)

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
                        )

                self.stdout.write('Päätökset:')

                query = """
                    SELECT *
                    FROM PAATOS
                    WHERE 1 = 1
                    """ + expanded_id_to_query_alku(id_parts)

                cursor.execute(query)
                paatos_rows = rows_to_dict_list(cursor)

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

                self.stdout.write('Sopimukset:')

                query = """
                    SELECT *
                    FROM SOPIMUS
                    WHERE 1 = 1
                    """ + expanded_id_to_query_alku(id_parts)

                cursor.execute(query)
                sopimus_rows = rows_to_dict_list(cursor)

                for contract_row in sopimus_rows:
                    # TODO: Other contract numbers
                    if not re.fullmatch(r'\d+', contract_row['SOPIMUS']):
                        continue

                    (contract, contract_created) = Contract.objects.get_or_create(
                        lease=lease,
                        type_id=1,  # Vuokrasopimus
                        contract_number=contract_row['SOPIMUS'],
                        signing_date=contract_row['ALLEKIRJPVM'].date() if contract_row['ALLEKIRJPVM'] else None,
                        signing_note=None,
                        is_readjustment_decision=bool(contract_row['JARJESTELYPAATOS']),
                        collateral_number=contract_row['VUOKRAKIINNITYSPYKALA'],
                        collateral_start_date=contract_row['VUOKRAKIINNITYSPVM'],
                        collateral_end_date=contract_row['VUOKRAKIINNITYSLOPPUPVM'],
                        collateral_note=contract_row['KOMMENTTI'],
                        institution_identifier=contract_row['LAITOSTUNNUS'],
                    )

                    (mortgage_document, mortgage_document_created) = MortgageDocument.objects.get_or_create(
                        contract=contract,
                        number=contract_row['PYSYVYYSKIINNITYSPYKALA'],
                        date=contract_row['PYSYVYYSKIINNITYSPVM'].date() if contract_row[
                            'PYSYVYYSKIINNITYSPVM'] else None,
                        note=None
                    )

                    query = """
                        SELECT *
                        FROM SOPIMUS_MUUTOS
                        WHERE SOPIMUS = '{}'
                        """.format(contract_row['SOPIMUS'])

                    cursor.execute(query)
                    sopimus_muutos_rows = rows_to_dict_list(cursor)

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

    def update_related_leases(self):
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

    def update_credit_notes(self):
        self.stdout.write('Updating credit notes:')
        for credit_note_datum in self.credit_notes:
            credit_note = credit_note_datum['credit_note']
            if credit_note_datum['credited_invoice_id']:
                credit_note.credited_invoice_id = credit_note_datum['credited_invoice_id']
                credit_note.save()
            else:
                try:
                    credited_invoice = Invoice.objects.get(number=credit_note_datum['credited_invoice_number'])
                    credit_note.credited_invoice_id = credited_invoice.id
                    credit_note.save()
                except Invoice.DoesNotExist:
                    self.stdout.write("Credited invoice number #{} does not exist".format(
                        credit_note_datum['credited_invoice_number']))
                except Invoice.MultipleObjectsReturned:
                    self.stdout.write("Multiple invoices returned fot Credited invoice number #{}!".format(
                        credit_note_datum['credited_invoice_number']))
