import datetime
import re
from decimal import ROUND_HALF_UP, Decimal
from itertools import chain, groupby

from auditlog.registry import auditlog
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import connection, models, transaction
from django.db.models import Max, Q
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from field_permissions.registry import field_permissions
from leasing.enums import (
    Classification, DueDatesPosition, InvoiceState, InvoiceType, LeaseRelationType, LeaseState, NoticePeriodType)
from leasing.models import Contact
from leasing.models.mixins import NameModel, TimeStampedModel, TimeStampedSafeDeleteModel
from leasing.models.utils import (
    combine_ranges, fix_amount_for_overlap, get_range_overlap_and_remainder, subtract_ranges_from_ranges)
from users.models import User


class LeaseType(NameModel):
    """
    In Finnish: Laji
    """
    identifier = models.CharField(verbose_name=_("Identifier"), max_length=255, unique=True)
    sap_material_code = models.CharField(verbose_name=_("SAP material code"), null=True, blank=True, max_length=255)
    sap_order_item_number = models.CharField(verbose_name=_("SAP order item number"), null=True, blank=True,
                                             max_length=255)
    due_dates_position = EnumField(DueDatesPosition, verbose_name=_("Due dates position"),
                                   default=DueDatesPosition.START_OF_MONTH, max_length=30)

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Lease type")
        verbose_name_plural = pgettext_lazy("Model name", "Lease types")

    def __str__(self):
        return '{} ({})'.format(self.name, self.identifier)


class Municipality(NameModel):
    """
    In Finnish: Kaupunki
    """
    identifier = models.CharField(verbose_name=_("Identifier"), max_length=255, unique=True)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Municipality")
        verbose_name_plural = pgettext_lazy("Model name", "Municipalities")
        ordering = ['id']

    def __str__(self):
        return '{} ({})'.format(self.name, self.identifier)


class District(NameModel):
    """
    In Finnish: Kaupunginosa
    """
    municipality = models.ForeignKey(Municipality, verbose_name=_("Municipality"), related_name='districts',
                                     on_delete=models.PROTECT)
    identifier = models.CharField(verbose_name=_("Identifier"), max_length=255)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "District")
        verbose_name_plural = pgettext_lazy("Model name", "Districts")
        unique_together = ('municipality', 'identifier')
        ordering = ('municipality__name', 'name')

    def __str__(self):
        return '{} ({})'.format(self.name, self.identifier)


class IntendedUse(NameModel):
    """
    In Finnish: Käyttötarkoitus
    """
    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Intended use")
        verbose_name_plural = pgettext_lazy("Model name", "Intended uses")


class StatisticalUse(NameModel):
    """
    In Finnish: Tilastollinen pääkäyttötarkoitus
    """
    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Statistical use")
        verbose_name_plural = pgettext_lazy("Model name", "Statistical uses")


class SupportiveHousing(NameModel):
    """
    In Finnish: Erityisasunnot
    """
    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Supportive housing")
        verbose_name_plural = pgettext_lazy("Model name", "Supportive housings")


class Financing(NameModel):
    """
    In Finnish: Rahoitusmuoto
    """
    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Form of financing")
        verbose_name_plural = pgettext_lazy("Model name", "Forms of financing")


class Management(NameModel):
    """
    In Finnish: Hallintamuoto
    """
    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Form of management")
        verbose_name_plural = pgettext_lazy("Model name", "Forms of management")


class Regulation(NameModel):
    """
    In Finnish: Sääntelymuoto
    """
    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Form of regulation")
        verbose_name_plural = pgettext_lazy("Model name", "Forms of regulation")


class Hitas(NameModel):
    """
    In Finnish: Hitas
    """
    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Hitas")
        verbose_name_plural = pgettext_lazy("Model name", "Hitas")


class NoticePeriod(NameModel):
    """
    In Finnish: Irtisanomisaika
    """
    type = EnumField(NoticePeriodType, verbose_name=_("Period type"), max_length=30)
    duration = models.CharField(verbose_name=_("Duration"), null=True, blank=True, max_length=255,
                                help_text=_("In ISO 8601 Duration format"))

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Notice period")
        verbose_name_plural = pgettext_lazy("Model name", "Notice periods")


class SpecialProject(NameModel):
    """
    In Finnish: Erityishanke
    """
    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Special project")
        verbose_name_plural = pgettext_lazy("Model name", "Special projects")


class LeaseIdentifier(TimeStampedSafeDeleteModel):
    """
    In Finnish: Vuokraustunnus
    """
    # In Finnish: Laji
    type = models.ForeignKey(LeaseType, verbose_name=_("Lease type"), on_delete=models.PROTECT)

    # In Finnish: Kaupunki
    municipality = models.ForeignKey(Municipality, verbose_name=_("Municipality"), on_delete=models.PROTECT)

    # In Finnish: Kaupunginosa
    district = models.ForeignKey(District, verbose_name=_("District"), on_delete=models.PROTECT)

    # In Finnish: Juokseva numero
    sequence = models.PositiveIntegerField(verbose_name=_("Sequence number"))

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Lease identifier")
        verbose_name_plural = pgettext_lazy("Model name", "Lease identifiers")
        unique_together = ('type', 'municipality', 'district', 'sequence')

    def __str__(self):
        """Returns the lease identifier as a string

        The lease identifier is constructed out of type, municipality,
        district, and sequence, in that order. For example, the identifier
        for a residence (A1) in Helsinki (1), Vallila (22), and sequence
        number 1 would be A1122-1.
        """
        return '{}{}{:02}-{}'.format(self.type.identifier, self.municipality.identifier, int(self.district.identifier),
                                     self.sequence)


class LeaseManager(models.Manager):
    def full_select_related_and_prefetch_related(self):
        return self.get_queryset().select_related(
            'type', 'municipality', 'district', 'identifier', 'identifier__type', 'identifier__municipality',
            'identifier__district', 'lessor', 'intended_use', 'supportive_housing', 'statistical_use', 'financing',
            'management', 'regulation', 'hitas', 'notice_period', 'preparer'
        ).prefetch_related(
            'tenants', 'tenants__tenantcontact_set', 'tenants__tenantcontact_set__contact',
            'lease_areas', 'contracts', 'decisions', 'inspections', 'rents', 'rents__due_dates',
            'rents__contract_rents', 'rents__contract_rents__intended_use', 'rents__rent_adjustments',
            'rents__rent_adjustments__intended_use', 'rents__index_adjusted_rents', 'rents__payable_rents',
            'rents__fixed_initial_year_rents', 'rents__fixed_initial_year_rents__intended_use',
            'lease_areas__addresses', 'basis_of_rents', 'collection_letters', 'collection_notes',
            'collection_court_decisions'
        )

    def succinct_select_related_and_prefetch_related(self):
        return self.get_queryset().select_related(
            'type', 'municipality', 'district', 'identifier', 'identifier__type',
            'identifier__municipality', 'identifier__district', 'preparer').prefetch_related('related_leases')

    def get_by_identifier(self, identifier):
        id_match = re.match(r'(?P<lease_type>\w\d)(?P<municipality>\d)(?P<district>\d{2})-(?P<sequence>\d+)$',
                            identifier)

        if not id_match:
            raise RuntimeError('identifier "{}" doesn\'t match the identifier format'.format(identifier))

        # TODO: Kludge
        district = id_match.group('district')
        if district == '00':
            district = '0'
        else:
            district = district.lstrip('0')

        return self.get_queryset().get(identifier__type__identifier=id_match.group('lease_type'),
                                       identifier__municipality__identifier=id_match.group('municipality'),
                                       identifier__district__identifier=district,
                                       identifier__sequence=id_match.group('sequence').lstrip('0'))


class Lease(TimeStampedSafeDeleteModel):
    """
    In Finnish: Vuokraus
    """
    # Identifier fields
    # In Finnish: Laji
    type = models.ForeignKey(LeaseType, verbose_name=_("Lease type"), on_delete=models.PROTECT)

    # In Finnish: Kaupunki
    municipality = models.ForeignKey(Municipality, verbose_name=_("Municipality"), on_delete=models.PROTECT)

    # In Finnish: Kaupunginosa
    district = models.ForeignKey(District, verbose_name=_("District"), on_delete=models.PROTECT)

    # In Finnish: Vuokratunnus
    identifier = models.OneToOneField(LeaseIdentifier, verbose_name=_("Lease identifier"), null=True, blank=True,
                                      on_delete=models.PROTECT)

    # Other fields
    # In Finnish: Alkupäivämäärä
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)

    # In Finnish: Loppupäivämäärä
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    # In Finnish: Tila
    state = EnumField(LeaseState, verbose_name=_("State"), null=True, blank=True, max_length=30)

    # In Finnish: Julkisuusluokka
    classification = EnumField(Classification, verbose_name=_("Classification"), null=True, blank=True, max_length=30)

    # In Finnish: Käyttötarkoituksen selite
    intended_use_note = models.TextField(verbose_name=_("Intended use note"), null=True, blank=True)

    # In Finnish: Siirto-oikeus
    transferable = models.BooleanField(verbose_name=_("Transferable"), null=True, blank=True, default=None)

    # In Finnish: Säännelty
    regulated = models.BooleanField(verbose_name=_("Regulated"), default=False)

    # In Finnish: Irtisanomisilmoituksen selite
    notice_note = models.TextField(verbose_name=_("Notice note"), null=True, blank=True)

    # Relations
    # In Finnish: Vuokranantaja
    lessor = models.ForeignKey(Contact, verbose_name=_("Lessor"), null=True, blank=True, on_delete=models.PROTECT)

    # In Finnish: Käyttötarkoitus
    intended_use = models.ForeignKey(IntendedUse, verbose_name=_("Intended use"), null=True, blank=True,
                                     on_delete=models.PROTECT)

    # In Finnish: Erityisasunnot
    supportive_housing = models.ForeignKey(SupportiveHousing, verbose_name=_("Supportive housing"), null=True,
                                           blank=True, on_delete=models.PROTECT)

    # In Finnish: Tilastollinen pääkäyttötarkoitus
    statistical_use = models.ForeignKey(StatisticalUse, verbose_name=_("Statistical use"), null=True, blank=True,
                                        on_delete=models.PROTECT)

    # In Finnish: Rahoitusmuoto
    financing = models.ForeignKey(Financing, verbose_name=_("Form of financing"), null=True, blank=True,
                                  on_delete=models.PROTECT)

    # In Finnish: Hallintamuoto
    management = models.ForeignKey(Management, verbose_name=_("Form of management"), null=True, blank=True,
                                   on_delete=models.PROTECT)

    # In Finnish: Sääntelymuoto
    regulation = models.ForeignKey(Regulation, verbose_name=_("Form of regulation"), null=True, blank=True,
                                   on_delete=models.PROTECT)
    # In Finnish: Hitas
    hitas = models.ForeignKey(Hitas, verbose_name=_("Hitas"), null=True, blank=True, on_delete=models.PROTECT)

    # In Finnish: Irtisanomisaika
    notice_period = models.ForeignKey(NoticePeriod, verbose_name=_("Notice period"), null=True, blank=True,
                                      on_delete=models.PROTECT)

    related_leases = models.ManyToManyField('self', through='leasing.RelatedLease', symmetrical=False,
                                            related_name='related_to')

    # In Finnish: Vuokratiedot kunnossa
    is_rent_info_complete = models.BooleanField(verbose_name=_("Rent info complete?"), default=False)

    # In Finnish: Laskutus käynnissä
    is_invoicing_enabled = models.BooleanField(verbose_name=_("Invoicing enabled?"), default=False)

    # In Finnish: Diaarinumero
    reference_number = models.CharField(verbose_name=_("Reference number"), null=True, blank=True, max_length=255)

    # In Finnish: Kommentti
    note = models.TextField(verbose_name=_("Note"), null=True, blank=True)

    # In Finnish: Valmistelija
    preparer = models.ForeignKey(User, verbose_name=_("Preparer"), null=True, blank=True, on_delete=models.PROTECT)

    # In Finnish: Onko ALV:n alainen
    is_subject_to_vat = models.BooleanField(verbose_name=_("Is subject to VAT?"), default=False)

    # In Finnish: Rakennuttaja
    real_estate_developer = models.CharField(verbose_name=_("Real estate developer"), null=True, blank=True,
                                             max_length=255)

    # In Finnish: Luovutusnumero
    conveyance_number = models.CharField(verbose_name=_("Conveyance number"), null=True, blank=True,
                                         max_length=255)

    # In Finnish: Rakennuksen kauppahinta
    building_selling_price = models.DecimalField(verbose_name=_("Building selling price"), null=True, blank=True,
                                                 max_digits=10, decimal_places=2)

    # In Finnish: Erityishanke
    special_project = models.ForeignKey(SpecialProject, verbose_name=_("Special project"), null=True, blank=True,
                                        on_delete=models.PROTECT)

    # In Finnish: Järjestelypäätös
    arrangement_decision = models.BooleanField(verbose_name=_("Arrangement decision"), null=True, blank=True,
                                               default=None)

    objects = LeaseManager()

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Lease")
        verbose_name_plural = pgettext_lazy("Model name", "Leases")

    def __str__(self):
        return self.get_identifier_string()

    def get_identifier_string(self):
        if self.identifier:
            return str(self.identifier)
        else:
            return '{}{}{:02}-'.format(
                self.type.identifier, self.municipality.identifier, int(self.district.identifier))

    @transaction.atomic
    def create_identifier(self):
        if self.identifier_id:
            return

        if not self.type or not self.municipality or not self.district:
            return

        # lock LeaseIdentifier table to prevent a (theoretically) possible race condition
        # when increasing the sequence
        with connection.cursor() as cursor:
            cursor.execute('LOCK TABLE %s' % self._meta.db_table)

        max_sequence = LeaseIdentifier.objects.filter(
            type=self.type,
            municipality=self.municipality,
            district=self.district).aggregate(Max('sequence'))['sequence__max']

        if not max_sequence:
            max_sequence = 0

        lease_identifier = LeaseIdentifier.objects.create(
            type=self.type,
            municipality=self.municipality,
            district=self.district,
            sequence=max_sequence + 1)

        self.identifier = lease_identifier

    def save(self, *args, **kwargs):
        self.create_identifier()

        super().save(*args, **kwargs)

    def get_due_dates_for_period(self, start_date, end_date):
        due_dates = set()

        range_filtering = Q(
            Q(Q(end_date=None) | Q(end_date__gte=start_date)) &
            Q(Q(start_date=None) | Q(start_date__lte=end_date))
        )

        for rent in self.rents.filter(range_filtering):
            due_dates.update(rent.get_due_dates_for_period(start_date, end_date))

        return sorted(due_dates)

    def get_tenant_shares_for_period(self, billing_period_start_date, billing_period_end_date):  # noqa C901 TODO
        tenant_range_filter = Q(
            Q(Q(tenantcontact__end_date=None) | Q(tenantcontact__end_date__gte=billing_period_start_date)) &
            Q(Q(tenantcontact__start_date=None) | Q(tenantcontact__start_date__lte=billing_period_end_date)) &
            Q(tenantcontact__deleted__isnull=True)
        )

        shares = {}
        for tenant in self.tenants.filter(tenant_range_filter).distinct():
            tenant_tenantcontacts = tenant.get_tenant_tenantcontacts(billing_period_start_date, billing_period_end_date)
            billing_tenantcontacts = tenant.get_billing_tenantcontacts(billing_period_start_date,
                                                                       billing_period_end_date)

            if not tenant_tenantcontacts or not billing_tenantcontacts:
                raise Exception('No suitable contacts in the period {} - {}'.format(billing_period_start_date,
                                                                                    billing_period_end_date))

            (tenant_overlap, tenant_remainders) = get_range_overlap_and_remainder(
                billing_period_start_date, billing_period_end_date, *tenant_tenantcontacts[0].date_range)

            if not tenant_overlap:
                raise Exception('No overlap with this billing period. Error?')

            for billing_tenantcontact in billing_tenantcontacts:
                (billing_overlap, billing_remainders) = get_range_overlap_and_remainder(
                    tenant_overlap[0], tenant_overlap[1], *billing_tenantcontact.date_range)

                if not billing_overlap:
                    continue

                if billing_tenantcontact.contact not in shares:
                    shares[billing_tenantcontact.contact] = {}

                if tenant not in shares[billing_tenantcontact.contact]:
                    shares[billing_tenantcontact.contact][tenant] = []

                shares[billing_tenantcontact.contact][tenant].append(billing_overlap)

            ranges_for_billing_contacts = []
            for billing_contact, tenant_overlaps in shares.items():
                if tenant in tenant_overlaps:
                    ranges_for_billing_contacts.extend(tenant_overlaps[tenant])

            leftover_ranges = subtract_ranges_from_ranges([tenant_overlap], ranges_for_billing_contacts)

            if leftover_ranges:
                # TODO: Which tenantcontact to use when multiple tenantcontacts
                if tenant_tenantcontacts[0].contact not in shares:
                    shares[tenant_tenantcontacts[0].contact] = {
                        tenant: [],
                    }
                shares[tenant_tenantcontacts[0].contact][tenant].extend(leftover_ranges)

        return shares

    def get_lease_info_text(self, tenants=None):
        today = datetime.date.today()
        result = []

        if tenants is None:
            tenants = self.tenants.all()

        tenant_names = []
        for tenant in tenants:
            for tenant_tenantcontact in tenant.get_tenant_tenantcontacts(today, today):
                tenant_names.append(tenant_tenantcontact.contact.get_name_and_identifier())

        result.extend(tenant_names)

        area_names = []
        for lease_area in self.lease_areas.all():
            area_names.append(_('{area_identifier}, {area_addresses}, {area_m2}m2').format(
                area_identifier=lease_area.identifier,
                area_addresses=', '.join([la.address for la in lease_area.addresses.all()]),
                area_m2=lease_area.area
            ))

        result.extend(area_names)

        contract_numbers = []
        for contract in self.contracts.filter(contract_number__isnull=False).exclude(contract_number=''):
            contract_numbers.append(_('Contract #{contract_number}').format(contract_number=contract.contract_number))

        result.extend(contract_numbers)

        return result

    def get_active_rents_on_period(self, date_range_start, date_range_end):
        rent_range_filter = Q(
            Q(Q(end_date=None) | Q(end_date__gte=date_range_start)) &
            Q(Q(start_date=None) | Q(start_date__lte=date_range_end))
        )

        return self.rents.filter(rent_range_filter)

    def get_rent_amount_and_explations_for_period(self, start_date, end_date):
        amount = Decimal(0)
        explanations = []

        for rent in self.get_active_rents_on_period(start_date, end_date):
            (this_amount, explanation) = rent.get_amount_for_date_range(start_date, end_date, explain=True)

            amount += this_amount
            explanations.append(explanation)

        return amount, explanations

    def get_rent_amount_for_year(self, year):
        first_day_of_year = datetime.date(year=year, month=1, day=1)
        last_day_of_year = datetime.date(year=year, month=12, day=31)

        (year_rent, explanations) = self.get_rent_amount_and_explations_for_period(first_day_of_year, last_day_of_year)

        return year_rent

    def determine_payable_rents_and_periods(self, start_date, end_date):
        lease_due_dates = self.get_due_dates_for_period(start_date, end_date)

        if not lease_due_dates:
            # TODO
            return {}

        amounts_for_billing_periods = {}

        for lease_due_date in lease_due_dates:
            for rent in self.get_active_rents_on_period(start_date, end_date):
                billing_period = rent.get_billing_period_from_due_date(lease_due_date)

                if not billing_period:
                    continue

                # Ignore periods that occur before the lease start date or after the lease end date
                if ((self.start_date and billing_period[1] < self.start_date) or
                        (self.end_date and billing_period[0] > self.end_date)):
                    continue

                # Adjust billing period start to the lease start date if needed
                if self.start_date and billing_period[0] < self.start_date:
                    billing_period = (self.start_date, billing_period[1])

                # Adjust billing period end to the lease end date if needed
                if self.end_date and billing_period[1] > self.end_date:
                    billing_period = (billing_period[0], self.end_date)

                if billing_period not in amounts_for_billing_periods:
                    amounts_for_billing_periods[billing_period] = {
                        'due_date': lease_due_date,
                        'amount': Decimal(0),
                        'explanations': [],
                    }

                (this_amount, explanation) = rent.get_amount_for_date_range(*billing_period, explain=True)

                amounts_for_billing_periods[billing_period]['amount'] += this_amount
                amounts_for_billing_periods[billing_period]['explanations'].append(explanation)

        return amounts_for_billing_periods

    def calculate_invoices(self, period_rents):
        from leasing.models import ReceivableType

        # TODO: Make configurable
        receivable_type_rent = ReceivableType.objects.get(pk=1)

        # rents = self.determine_payable_rents_and_periods(self.start_date, self.end_date)

        invoice_data = []

        for billing_period, period_rent in period_rents.items():
            billing_period_invoices = []
            rent_amount = period_rent['amount']

            shares = self.get_tenant_shares_for_period(*billing_period)

            for contact, share in shares.items():
                billable_amount = Decimal(0)
                contact_ranges = []
                invoice_row_data = []

                for tenant, overlaps in share.items():
                    overlap_amount = Decimal(0)
                    for overlap in overlaps:
                        overlap_amount += fix_amount_for_overlap(
                            rent_amount, overlap, subtract_ranges_from_ranges([billing_period], [overlap]))

                        share_amount = Decimal(
                            overlap_amount * Decimal(tenant.share_numerator / tenant.share_denominator)
                        ).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)

                        billable_amount += share_amount

                        contact_ranges.append(overlap)
                        invoice_row_data.append({
                            'tenant': tenant,
                            'receivable_type': receivable_type_rent,
                            'billing_period_start_date': overlap[0],
                            'billing_period_end_date': overlap[1],
                            'amount': share_amount,
                        })

                combined_contact_ranges = combine_ranges(contact_ranges)

                total_contact_period_amount = Decimal(0)
                for combined_contact_range in combined_contact_ranges:
                    total_contact_period_amount += fix_amount_for_overlap(
                        rent_amount, combined_contact_range, subtract_ranges_from_ranges(
                            [billing_period], [combined_contact_range]))

                total_contact_period_amount = Decimal(total_contact_period_amount).quantize(Decimal('.01'),
                                                                                            rounding=ROUND_HALF_UP)

                invoice_datum = {
                    'type': InvoiceType.CHARGE,
                    'lease': self,
                    'recipient': contact,
                    'due_date': period_rent['due_date'],
                    'billing_period_start_date': billing_period[0],
                    'billing_period_end_date': billing_period[1],
                    'total_amount': total_contact_period_amount,
                    'billed_amount': billable_amount,
                    'rows': invoice_row_data,
                    'explanations': period_rent['explanations'],
                    'state': InvoiceState.OPEN,
                }

                billing_period_invoices.append(invoice_datum)

            invoice_data.append(billing_period_invoices)

        return invoice_data

    def generate_first_invoices(self, end_date=None):  # noqa C901 TODO
        from leasing.models.invoice import Invoice, InvoiceRow, InvoiceSet
        today = datetime.date.today()

        if not self.start_date:
            # TODO: Emit error
            return []

        if not end_date:
            end_date = today if not self.end_date or self.end_date >= today else self.end_date

        years = range(self.start_date.year, end_date.year + 1)

        if not years:
            return []

        lease_due_dates = self.get_due_dates_for_period(datetime.date(year=min(years), month=1, day=1),
                                                        datetime.date(year=max(years) + 1, month=1, day=31))

        amounts_for_billing_periods = {}
        # Calculate amounts for all the billing periods that have
        # occurred before the next possible invoicing day.
        # TODO: merge with lease.determine_payable_rents_and_periods
        for due_date in lease_due_dates:
            due_date_invoicing_date = due_date - relativedelta(months=1, day=1)

            # Don't include due dates that have an upcoming invoicing date
            if due_date_invoicing_date > end_date:
                continue

            for rent in self.get_active_rents_on_period(self.start_date, end_date):
                billing_period = rent.get_billing_period_from_due_date(due_date)

                if not billing_period:
                    continue

                # Ignore periods that occur before the lease start date or after the lease end date
                if ((self.start_date and billing_period[1] < self.start_date) or
                        (self.end_date and billing_period[0] > self.end_date)):
                    continue

                # Adjust billing period start to the lease start date if needed
                if billing_period[0] < self.start_date:
                    billing_period = (self.start_date, billing_period[1])

                # Adjust billing period end to the lease end date if needed
                if self.end_date and billing_period[1] > self.end_date:
                    billing_period = (billing_period[0], self.end_date)

                if billing_period not in amounts_for_billing_periods:
                    amounts_for_billing_periods[billing_period] = {
                        'due_date': due_date,
                        'amount': Decimal(0),
                        'explanations': [],
                    }

                (this_amount, explanation) = rent.get_amount_for_date_range(*billing_period, explain=True)

                amounts_for_billing_periods[billing_period]['amount'] += this_amount
                amounts_for_billing_periods[billing_period]['explanations'].append(explanation)

        invoice_data = self.calculate_invoices(amounts_for_billing_periods)

        # Flatten and sort the data
        invoice_data = sorted(chain(*invoice_data), key=lambda x: x.get('recipient').id)

        # Calculate total and determine the longest billing period
        total_total_amount = Decimal(0)
        recipients = set()
        billing_period_start_date = datetime.date(year=2500, day=1, month=1)
        billing_period_end_date = datetime.date(year=2000, day=1, month=1)
        for invoice_datum in invoice_data:
            total_total_amount += invoice_datum['billed_amount']
            recipients.add(invoice_datum['recipient'])
            billing_period_start_date = min(invoice_datum['billing_period_start_date'], billing_period_start_date)
            billing_period_end_date = max(invoice_datum['billing_period_end_date'], billing_period_end_date)

        new_due_date = today + relativedelta(days=settings.MVJ_DUE_DATE_OFFSET_DAYS)

        invoiceset = None
        if len(recipients) > 1:
            try:
                invoiceset = InvoiceSet.objects.get(lease=self, billing_period_start_date=billing_period_start_date,
                                                    billing_period_end_date=billing_period_end_date)
            except InvoiceSet.DoesNotExist:
                invoiceset = InvoiceSet.objects.create(lease=self, billing_period_start_date=billing_period_start_date,
                                                       billing_period_end_date=billing_period_end_date)

        # Group by recipient and generate merged invoices
        invoices = []
        for recipient, recipient_invoice_data in groupby(invoice_data, key=lambda x: x.get('recipient')):
            total_billed_amount = Decimal(0)
            billing_period_start_date = datetime.date(year=2500, day=1, month=1)
            billing_period_end_date = datetime.date(year=2000, day=1, month=1)
            rows = []

            for recipient_invoice_datum in recipient_invoice_data:
                billing_period_start_date = min(recipient_invoice_datum['billing_period_start_date'],
                                                billing_period_start_date)
                billing_period_end_date = max(recipient_invoice_datum['billing_period_end_date'],
                                              billing_period_end_date)
                total_billed_amount += recipient_invoice_datum['billed_amount']
                rows.extend(recipient_invoice_datum['rows'])

            invoice_data = {
                'lease': self,
                'invoicing_date': today,
                'billing_period_start_date': billing_period_start_date,
                'billing_period_end_date': billing_period_end_date,
                'billed_amount': total_billed_amount,
                'outstanding_amount': total_billed_amount,
                'total_amount': total_total_amount,
                'state': InvoiceState.OPEN,
                'type': InvoiceType.CHARGE,
                'due_date': new_due_date,
                'recipient': recipient,
                'invoiceset': invoiceset,
                'generated': True,
            }

            try:
                invoice = Invoice.objects.get(**invoice_data)
            except Invoice.DoesNotExist:
                invoice = Invoice.objects.create(**invoice_data)

                for row in rows:
                    row['invoice'] = invoice
                    InvoiceRow.objects.create(**row)

            invoices.append(invoice)

        return invoices

    def credit_rent_after_end(self):
        from leasing.models.invoice import Invoice, InvoiceRow

        if not self.end_date:
            return

        today = datetime.date.today()

        invoices = Invoice.objects.filter(generated=True, type=InvoiceType.CHARGE, state=InvoiceState.PAID,
                                          billing_period_end_date__gt=self.end_date)

        for invoice in invoices:
            extra_start_date = self.end_date + relativedelta(days=1)
            extra_end_date = invoice.billing_period_end_date
            extra_billing_period = (extra_start_date, extra_end_date)

            (extra_amount, tmp) = self.get_rent_amount_and_explations_for_period(extra_start_date, extra_end_date)

            amounts_for_billing_periods = {
                extra_billing_period: {
                    'due_date': today,
                    'amount': extra_amount,
                    'explanations': [],
                }
            }

            new_invoice_data = self.calculate_invoices(amounts_for_billing_periods)

            for period_invoice_data in new_invoice_data:
                for invoice_data in period_invoice_data:
                    invoice_data.pop('explanations')

                    # Match the invoice
                    if not invoice.is_same_recipient_and_tenants(invoice_data):
                        # TODO: What if not found
                        continue

                    invoice_data['type'] = InvoiceType.CREDIT_NOTE
                    invoice_data['state'] = InvoiceState.PAID
                    invoice_data['generated'] = True
                    invoice_data['invoiceset'] = invoice.invoiceset
                    invoice_row_data = invoice_data.pop('rows')

                    try:
                        credit_note = Invoice.objects.get(**invoice_data)
                    except Invoice.DoesNotExist:
                        with transaction.atomic():
                            invoice_data['invoicing_date'] = today

                            credit_note = Invoice.objects.create(**invoice_data)

                            for invoice_row_datum in invoice_row_data:
                                invoice_row_datum['invoice'] = credit_note
                                InvoiceRow.objects.create(**invoice_row_datum)

                            invoice.update_amounts()
                    except Invoice.MultipleObjectsReturned:
                        pass

    def set_is_invoicing_enabled(self, state):
        if self.is_invoicing_enabled is state:
            return

        if state is True:
            # TODO: Check that rents, tenants, etc. are in order
            self.is_invoicing_enabled = True
            self.save()

            self.generate_first_invoices()
        else:
            self.is_invoicing_enabled = False
            self.save()

    def set_is_rent_info_complete(self, state):
        if self.is_rent_info_complete is state:
            return

        # TODO: Notify billing
        self.is_rent_info_complete = state
        self.save()


class LeaseStateLog(TimeStampedModel):
    lease = models.ForeignKey(Lease, verbose_name=_("Lease"), on_delete=models.PROTECT)
    state = EnumField(LeaseState, verbose_name=_("State"), max_length=30)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Lease state log")
        verbose_name_plural = pgettext_lazy("Model name", "Lease state logs")


class RelatedLease(TimeStampedSafeDeleteModel):
    from_lease = models.ForeignKey(Lease, verbose_name=_("From lease"), related_name='from_leases',
                                   on_delete=models.PROTECT)
    to_lease = models.ForeignKey(Lease, verbose_name=_("To lease"), related_name='to_leases', on_delete=models.PROTECT)
    type = EnumField(LeaseRelationType, verbose_name=_("Lease relation type"), null=True, blank=True, max_length=30)
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Related lease")
        verbose_name_plural = pgettext_lazy("Model name", "Related leases")


auditlog.register(Lease)
auditlog.register(RelatedLease)

field_permissions.register(Lease, exclude_fields=[
    'from_leases', 'to_leases', 'leases', 'invoicesets', 'leasestatelog'])
