import re

from auditlog.registry import auditlog
from django.db import connection, models, transaction
from django.db.models import Max, Q
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import Classification, DueDatesPosition, LeaseRelationType, LeaseState, NoticePeriodType
from leasing.models import Contact
from leasing.models.mixins import NameModel, TimeStampedModel, TimeStampedSafeDeleteModel
from leasing.models.utils import get_range_overlap_and_remainder
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
            'lease_areas__addresses', 'basis_of_rents'
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
    transferable = models.BooleanField(verbose_name=_("Transferable"), default=True)

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

    def get_tenant_shares_for_period(self, billing_period_start_date, billing_period_end_date):
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
