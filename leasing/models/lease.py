import datetime
import re
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from itertools import chain, groupby
from random import choice

from auditlog.registry import auditlog
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import connection, models, transaction
from django.db.models import Max, Q
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from enumfields import EnumField
from safedelete.managers import SafeDeleteManager

from field_permissions.registry import field_permissions
from leasing.calculation.result import CalculationAmount, CalculationResult
from leasing.enums import (
    Classification,
    DueDatesPosition,
    InvoiceState,
    InvoiceType,
    LeaseRelationType,
    LeaseState,
    NoticePeriodType,
    TenantContactType,
)
from leasing.models import Contact
from leasing.models.invoice import InvoiceRow
from leasing.models.mixins import (
    NameModel,
    TimeStampedModel,
    TimeStampedSafeDeleteModel,
)
from leasing.models.utils import (
    fix_amount_for_overlap,
    get_range_overlap_and_remainder,
    is_instance_empty,
    subtract_ranges_from_ranges,
)
from users.models import User


class LeaseType(NameModel):
    """
    In Finnish: Laji
    """

    identifier = models.CharField(
        verbose_name=_("Identifier"), max_length=255, unique=True
    )
    sap_material_code = models.CharField(
        verbose_name=_("SAP material code"), null=True, blank=True, max_length=255
    )
    sap_order_item_number = models.CharField(
        verbose_name=_("SAP order item number"), null=True, blank=True, max_length=255
    )
    due_dates_position = EnumField(
        DueDatesPosition,
        verbose_name=_("Due dates position"),
        default=DueDatesPosition.START_OF_MONTH,
        max_length=30,
    )

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Lease type")
        verbose_name_plural = pgettext_lazy("Model name", "Lease types")

    def __str__(self):
        return "{} ({})".format(self.name, self.identifier)


class Municipality(NameModel):
    """
    In Finnish: Kaupunki
    """

    identifier = models.CharField(
        verbose_name=_("Identifier"), max_length=255, unique=True
    )

    recursive_get_related_skip_relations = ["districts"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Municipality")
        verbose_name_plural = pgettext_lazy("Model name", "Municipalities")
        ordering = ["id"]

    def __str__(self):
        return "{} ({})".format(self.name, self.identifier)


class District(NameModel):
    """
    In Finnish: Kaupunginosa
    """

    municipality = models.ForeignKey(
        Municipality,
        verbose_name=_("Municipality"),
        related_name="districts",
        on_delete=models.PROTECT,
    )
    identifier = models.CharField(verbose_name=_("Identifier"), max_length=255)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "District")
        verbose_name_plural = pgettext_lazy("Model name", "Districts")
        unique_together = ("municipality", "identifier")
        ordering = ("municipality__name", "name")

    def __str__(self):
        return "{} ({})".format(self.name, self.identifier)


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
    duration = models.CharField(
        verbose_name=_("Duration"),
        null=True,
        blank=True,
        max_length=255,
        help_text=_("In ISO 8601 Duration format"),
    )

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


class ReservationProcedure(NameModel):
    """
    In Finnish: Varauksen menettely
    """

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Reservation procedure")
        verbose_name_plural = pgettext_lazy("Model name", "Reservation Procedures")


class LeaseIdentifier(TimeStampedSafeDeleteModel):
    """
    In Finnish: Vuokraustunnus
    """

    # In Finnish: Tunnus
    identifier = models.CharField(
        verbose_name=_("Identifier"), max_length=255, blank=True, null=True
    )

    # In Finnish: Laji
    type = models.ForeignKey(
        LeaseType,
        verbose_name=_("Lease type"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Kaupunki
    municipality = models.ForeignKey(
        Municipality,
        verbose_name=_("Municipality"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Kaupunginosa
    district = models.ForeignKey(
        District, verbose_name=_("District"), related_name="+", on_delete=models.PROTECT
    )

    # In Finnish: Juokseva numero
    sequence = models.PositiveIntegerField(verbose_name=_("Sequence number"))

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Lease identifier")
        verbose_name_plural = pgettext_lazy("Model name", "Lease identifiers")
        unique_together = ("type", "municipality", "district", "sequence")

    def save(self, *args, **kwargs):
        self.identifier = str(self)
        super(LeaseIdentifier, self).save(*args, **kwargs)

    def __str__(self):
        """Returns the lease identifier as a string

        The lease identifier is constructed out of type, municipality,
        district, and sequence, in that order. For example, the identifier
        for a residence (A1) in Helsinki (1), Vallila (22), and sequence
        number 1 would be A1122-1.
        """
        return "{}{}{:02}-{}".format(
            self.type.identifier,
            self.municipality.identifier,
            int(self.district.identifier),
            self.sequence,
        )


class LeaseManager(SafeDeleteManager):
    def full_select_related_and_prefetch_related(self):
        return (
            self.get_queryset()
            .select_related(
                "type",
                "municipality",
                "district",
                "identifier",
                "identifier__type",
                "identifier__municipality",
                "identifier__district",
                "lessor",
                "intended_use",
                "supportive_housing",
                "statistical_use",
                "financing",
                "management",
                "regulation",
                "hitas",
                "notice_period",
                "preparer",
            )
            .prefetch_related(
                "tenants",
                "tenants__rent_shares",
                "tenants__tenantcontact_set",
                "tenants__tenantcontact_set__contact",
                "lease_areas",
                "contracts",
                "decisions",
                "inspections",
                "rents",
                "rents__due_dates",
                "rents__contract_rents",
                "rents__contract_rents__intended_use",
                "rents__rent_adjustments",
                "rents__rent_adjustments__intended_use",
                "rents__index_adjusted_rents",
                "rents__payable_rents",
                "rents__fixed_initial_year_rents",
                "rents__fixed_initial_year_rents__intended_use",
                "lease_areas__addresses",
                "basis_of_rents",
                "collection_letters",
                "collection_notes",
                "collection_court_decisions",
                "invoice_notes",
            )
        )

    def succinct_select_related_and_prefetch_related(self):
        return self.get_queryset().select_related(
            "type",
            "municipality",
            "district",
            "identifier",
            "identifier__type",
            "identifier__municipality",
            "identifier__district",
            "preparer",
        )

    def get_by_identifier(self, identifier):
        id_match = re.match(
            r"(?P<lease_type>\w\d)(?P<municipality>\d)(?P<district>\d{2})-(?P<sequence>\d+)$",
            identifier,
        )

        if not id_match:
            raise RuntimeError(
                'identifier "{}" doesn\'t match the identifier format'.format(
                    identifier
                )
            )

        # TODO: Kludge
        district = id_match.group("district")
        if district == "00":
            district = "0"
        else:
            district = district.lstrip("0")

        return self.get_queryset().get(
            identifier__type__identifier=id_match.group("lease_type"),
            identifier__municipality__identifier=id_match.group("municipality"),
            identifier__district__identifier=district,
            identifier__sequence=id_match.group("sequence").lstrip("0"),
        )


class Lease(TimeStampedSafeDeleteModel):
    """
    In Finnish: Vuokraus
    """

    # Identifier fields
    # In Finnish: Laji
    type = models.ForeignKey(
        LeaseType,
        verbose_name=_("Lease type"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Kaupunki
    municipality = models.ForeignKey(
        Municipality,
        verbose_name=_("Municipality"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Kaupunginosa
    district = models.ForeignKey(
        District, verbose_name=_("District"), related_name="+", on_delete=models.PROTECT
    )

    # In Finnish: Vuokratunnus
    identifier = models.OneToOneField(
        LeaseIdentifier,
        verbose_name=_("Lease identifier"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # Other fields
    # In Finnish: Alkupäivämäärä
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)

    # In Finnish: Loppupäivämäärä
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    # In Finnish: Tila
    state = EnumField(
        LeaseState, verbose_name=_("State"), null=True, blank=True, max_length=30
    )

    # In Finnish: Julkisuusluokka
    classification = EnumField(
        Classification,
        verbose_name=_("Classification"),
        null=True,
        blank=True,
        max_length=30,
    )

    # In Finnish: Käyttötarkoituksen selite
    intended_use_note = models.TextField(
        verbose_name=_("Intended use note"), null=True, blank=True
    )

    # In Finnish: Siirto-oikeus
    transferable = models.BooleanField(
        verbose_name=_("Transferable"), null=True, blank=True, default=None
    )

    # In Finnish: Säännelty
    regulated = models.BooleanField(
        verbose_name=_("Regulated"), null=True, blank=True, default=None
    )

    # In Finnish: Irtisanomisilmoituksen selite
    notice_note = models.TextField(verbose_name=_("Notice note"), null=True, blank=True)

    # Relations
    # In Finnish: Vuokranantaja
    lessor = models.ForeignKey(
        Contact,
        verbose_name=_("Lessor"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Käyttötarkoitus
    intended_use = models.ForeignKey(
        IntendedUse,
        verbose_name=_("Intended use"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Erityisasunnot
    supportive_housing = models.ForeignKey(
        SupportiveHousing,
        verbose_name=_("Supportive housing"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Tilastollinen pääkäyttötarkoitus
    statistical_use = models.ForeignKey(
        StatisticalUse,
        verbose_name=_("Statistical use"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Rahoitusmuoto
    financing = models.ForeignKey(
        Financing,
        verbose_name=_("Form of financing"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Hallintamuoto
    management = models.ForeignKey(
        Management,
        verbose_name=_("Form of management"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Sääntelymuoto
    regulation = models.ForeignKey(
        Regulation,
        verbose_name=_("Form of regulation"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    # In Finnish: Hitas
    hitas = models.ForeignKey(
        Hitas,
        verbose_name=_("Hitas"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Irtisanomisaika
    notice_period = models.ForeignKey(
        NoticePeriod,
        verbose_name=_("Notice period"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    related_leases = models.ManyToManyField(
        "self",
        through="leasing.RelatedLease",
        symmetrical=False,
        related_name="related_to",
    )

    # In Finnish: Vuokratiedot kunnossa
    is_rent_info_complete = models.BooleanField(
        verbose_name=_("Rent info complete?"), default=False
    )

    # In Finnish: Laskutus käynnissä
    is_invoicing_enabled = models.BooleanField(
        verbose_name=_("Invoicing enabled?"), default=False
    )

    # In Finnish: Diaarinumero
    reference_number = models.CharField(
        verbose_name=_("Reference number"), null=True, blank=True, max_length=255
    )

    # In Finnish: Kommentti
    note = models.TextField(verbose_name=_("Note"), null=True, blank=True)

    # In Finnish: Valmistelija
    preparer = models.ForeignKey(
        User,
        verbose_name=_("Preparer"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Onko ALV:n alainen
    is_subject_to_vat = models.BooleanField(
        verbose_name=_("Is subject to VAT?"), default=False
    )

    # In Finnish: Rakennuttaja
    real_estate_developer = models.CharField(
        verbose_name=_("Real estate developer"), null=True, blank=True, max_length=255
    )

    # In Finnish: Luovutusnumero
    conveyance_number = models.CharField(
        verbose_name=_("Conveyance number"), null=True, blank=True, max_length=255
    )

    # In Finnish: Rakennuksen kauppahinta
    building_selling_price = models.DecimalField(
        verbose_name=_("Building selling price"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: Erityishanke
    special_project = models.ForeignKey(
        SpecialProject,
        verbose_name=_("Special project"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Varauksen menettely
    reservation_procedure = models.ForeignKey(
        ReservationProcedure,
        verbose_name=_("Reservation procedure"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    objects = LeaseManager()

    recursive_get_related_skip_relations = [
        "related_leases",
        "related_to",
        "from_leases",
        "to_leases",
    ]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Lease")
        verbose_name_plural = pgettext_lazy("Model name", "Leases")
        permissions = [("delete_nonempty_lease", "Can delete non-empty Lease")]

    def __str__(self):
        return self.get_identifier_string()

    def get_identifier_string(self):
        if self.identifier:
            return str(self.identifier)
        else:
            return "{}{}{:02}-".format(
                self.type.identifier,
                self.municipality.identifier,
                int(self.district.identifier),
            )

    @transaction.atomic
    def create_identifier(self):
        if self.identifier_id:
            return

        if not self.type or not self.municipality or not self.district:
            return

        # lock LeaseIdentifier table to prevent a (theoretically) possible race condition
        # when increasing the sequence
        with connection.cursor() as cursor:
            cursor.execute("LOCK TABLE %s" % self._meta.db_table)

        max_sequence = LeaseIdentifier.objects.filter(
            type=self.type, municipality=self.municipality, district=self.district
        ).aggregate(Max("sequence"))["sequence__max"]

        if not max_sequence:
            max_sequence = 0

        lease_identifier = LeaseIdentifier.objects.create(
            type=self.type,
            municipality=self.municipality,
            district=self.district,
            sequence=max_sequence + 1,
        )

        self.identifier = lease_identifier

    def save(self, *args, **kwargs):
        self.create_identifier()

        super().save(*args, **kwargs)

    def get_due_dates_for_period(self, start_date, end_date):
        due_dates = set()

        for rent in self.rents.all():
            due_dates.update(rent.get_due_dates_for_period(start_date, end_date))

        return sorted(due_dates)

    def get_tenant_shares_for_period(  # noqa C901 TODO
        self, period_start_date, period_end_date
    ):
        tenant_range_filter = Q(
            Q(
                Q(tenantcontact__end_date=None)
                | Q(tenantcontact__end_date__gte=period_start_date)
            )
            & Q(
                Q(tenantcontact__start_date=None)
                | Q(tenantcontact__start_date__lte=period_end_date)
            )
            & Q(tenantcontact__type=TenantContactType.TENANT)
            & Q(tenantcontact__deleted__isnull=True)
        )

        shares = {}
        for tenant in self.tenants.filter(tenant_range_filter).distinct():
            tenant_tenantcontacts = tenant.get_tenant_tenantcontacts(
                period_start_date, period_end_date
            )
            billing_tenantcontacts = tenant.get_billing_tenantcontacts(
                period_start_date, period_end_date
            )

            if not tenant_tenantcontacts or not billing_tenantcontacts:
                raise Exception(
                    "No suitable contacts in the period {} - {}".format(
                        period_start_date, period_end_date
                    )
                )

            (tenant_overlap, tenant_remainders) = get_range_overlap_and_remainder(
                period_start_date, period_end_date, *tenant_tenantcontacts[0].date_range
            )

            if not tenant_overlap:
                continue

            for billing_tenantcontact in billing_tenantcontacts:
                (billing_overlap, billing_remainders) = get_range_overlap_and_remainder(
                    tenant_overlap[0],
                    tenant_overlap[1],
                    *billing_tenantcontact.date_range
                )

                if not billing_overlap:
                    continue

                # Make sure that there are no multiple billing contacts for
                # the same tenant and period
                existing_overlaps = []
                for contact in shares:
                    for this_tenant, periods in shares[contact].items():
                        if this_tenant == tenant:
                            existing_overlaps.extend(periods)

                if billing_overlap in existing_overlaps:
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

            leftover_ranges = subtract_ranges_from_ranges(
                [tenant_overlap], ranges_for_billing_contacts
            )

            if leftover_ranges:
                # TODO: Which tenantcontact to use when multiple tenantcontacts
                contact = tenant_tenantcontacts[0].contact
                if contact not in shares:
                    shares[contact] = {}
                if tenant not in shares[contact]:
                    shares[contact][tenant] = []
                shares[contact][tenant].extend(leftover_ranges)

        return shares

    def get_lease_info_text(self, tenants=None):
        today = datetime.date.today()
        result = []

        if tenants is None:
            tenants = self.tenants.all()

        tenant_names = []
        for tenant in tenants:
            for tenant_tenantcontact in tenant.get_tenant_tenantcontacts(today, today):
                tenant_names.append(
                    tenant_tenantcontact.contact.get_name_and_identifier()
                )

        result.extend(tenant_names)

        area_names = []
        for lease_area in self.lease_areas.all():
            area_names.append(
                _("{area_identifier}, {area_addresses}, {area_m2}m2").format(
                    area_identifier=lease_area.identifier,
                    area_addresses=", ".join(
                        [la.address for la in lease_area.addresses.all()]
                    ),
                    area_m2=lease_area.area,
                )
            )

        result.extend(area_names)

        contract_numbers = []
        for contract in self.contracts.filter(contract_number__isnull=False).exclude(
            contract_number=""
        ):
            contract_numbers.append(
                _("Contract #{contract_number}").format(
                    contract_number=contract.contract_number
                )
            )

        result.extend(contract_numbers)

        return result

    def get_active_rents_on_period(self, date_range_start, date_range_end):
        rent_range_filter = Q(
            Q(Q(end_date=None) | Q(end_date__gte=date_range_start))
            & Q(Q(start_date=None) | Q(start_date__lte=date_range_end))
        )

        return self.rents.filter(rent_range_filter)

    # TODO: Create tests for this
    def get_all_billing_periods_for_year(self, year):
        date_range_start = datetime.date(year, 1, 1)
        date_range_end = datetime.date(year, 12, 31)

        billing_periods = set()
        for rent in self.get_active_rents_on_period(date_range_start, date_range_end):
            billing_periods.update(rent.get_all_billing_periods_for_year(year))

        billing_periods = sorted(list(billing_periods))

        return billing_periods

    # TODO: Create tests for this
    def is_the_last_billing_period(self, billing_period):
        billing_periods = self.get_all_billing_periods_for_year(billing_period[0].year)

        try:
            return billing_periods.index(billing_period) == len(billing_periods) - 1
        except ValueError:
            return False

    def calculate_rent_amount_for_period(self, start_date, end_date, dry_run=False):
        calculation_result = CalculationResult(
            date_range_start=start_date, date_range_end=end_date
        )

        for rent in self.get_active_rents_on_period(start_date, end_date):
            calculation_result.combine(
                rent.get_amount_for_date_range(start_date, end_date, dry_run=dry_run)
            )

        return calculation_result

    def calculate_rent_amount_for_year(self, year, dry_run=False):
        first_day_of_year = datetime.date(year=year, month=1, day=1)
        last_day_of_year = datetime.date(year=year, month=12, day=31)

        return self.calculate_rent_amount_for_period(
            first_day_of_year, last_day_of_year, dry_run=dry_run
        )

    def determine_payable_rents_and_periods(  # noqa: TODO
        self, start_date, end_date, dry_run=False, ignore_invoicing_date_after=None
    ):
        """Determines billing periods and rent amounts for them

        dry_run parameter is used when rent calculation is not for
        a real invoice. e.g. for only previewing the billing periods.
        The amount in an adjustment with the
        RentAdjustmentAmountType.AMOUNT_TOTAL-type is not updated
        when doing a dry run.

        ignore_invoicing_date_after -parameter can be used to limit
        calculation to only for the due dates that would be invoiced
        before the provided date.
        """
        lease_due_dates = self.get_due_dates_for_period(start_date, end_date)

        if not lease_due_dates:
            # TODO
            return {}

        amounts_for_billing_periods = {}

        for lease_due_date in lease_due_dates:
            if ignore_invoicing_date_after:
                due_date_invoicing_date = lease_due_date - relativedelta(
                    months=1, day=1
                )

                # Don't include due dates that have an upcoming invoicing date
                if due_date_invoicing_date > ignore_invoicing_date_after:
                    continue

            for rent in self.rents.all():
                billing_period = rent.get_billing_period_from_due_date(lease_due_date)

                if not billing_period:
                    continue

                if not rent.is_active_on_period(*billing_period):
                    continue

                # Ignore periods that occur before the lease start date or after the lease end date
                if (self.start_date and billing_period[1] < self.start_date) or (
                    self.end_date and billing_period[0] > self.end_date
                ):
                    continue

                # Adjust billing period start to the lease start date if needed
                if self.start_date and billing_period[0] < self.start_date:
                    billing_period = (self.start_date, billing_period[1])

                # Adjust billing period end to the lease end date if needed
                if self.end_date and billing_period[1] > self.end_date:
                    billing_period = (billing_period[0], self.end_date)

                if billing_period not in amounts_for_billing_periods:
                    amounts_for_billing_periods[billing_period] = {
                        "due_date": lease_due_date,
                        "calculation_result": CalculationResult(
                            date_range_start=start_date, date_range_end=end_date
                        ),
                        "last_billing_period": False,
                    }

                rent_calculation_result = rent.get_amount_for_date_range(
                    *billing_period, explain=True, dry_run=dry_run
                )

                if self.is_the_last_billing_period(billing_period):
                    amounts_for_billing_periods[billing_period][
                        "last_billing_period"
                    ] = True

                amounts_for_billing_periods[billing_period][
                    "calculation_result"
                ].combine(rent_calculation_result)

        return amounts_for_billing_periods

    def calculate_invoices(self, period_rents, dry_run=False):  # noqa: TODO
        from leasing.models import ReceivableType

        # TODO: Make configurable
        receivable_type_rent = ReceivableType.objects.get(pk=1)

        invoice_data = []
        last_billing_period = None

        for billing_period, period_rent in period_rents.items():
            contact_rows = defaultdict(list)

            if period_rent["last_billing_period"]:
                last_billing_period = billing_period

            for calculation_amount in period_rent[
                "calculation_result"
            ].get_all_amounts():
                amount_period = (
                    calculation_amount.date_range_start,
                    calculation_amount.date_range_end,
                )

                shares = self.get_tenant_shares_for_period(*amount_period)

                if not shares:
                    continue

                all_shares_total = Decimal(0)
                amount_rows = defaultdict(list)

                for contact, share in shares.items():
                    for tenant, overlaps in share.items():
                        rent_share = tenant.get_rent_share_by_intended_use(
                            calculation_amount.item.intended_use
                        )

                        if not rent_share:
                            continue

                        for overlap in overlaps:
                            overlap_amount = fix_amount_for_overlap(
                                calculation_amount.amount,
                                overlap,
                                subtract_ranges_from_ranges([amount_period], [overlap]),
                            )

                            share_amount = Decimal(
                                overlap_amount
                                * Decimal(
                                    rent_share.share_numerator
                                    / rent_share.share_denominator
                                )
                            ).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)

                            all_shares_total += share_amount

                            amount_rows[contact].append(
                                {
                                    "tenant": tenant,
                                    "receivable_type": receivable_type_rent,
                                    "intended_use": calculation_amount.item.intended_use,
                                    "billing_period_start_date": overlap[0],
                                    "billing_period_end_date": overlap[1],
                                    "amount": share_amount,
                                }
                            )

                # Add the difference to a random row in random contact if the total
                # of the rows doesn't match the amount. e.g. a rounding error.
                if all_shares_total != calculation_amount.amount:
                    difference = calculation_amount.amount - all_shares_total

                    if amount_rows:
                        random_contact = choice(list(amount_rows.keys()))
                        random_row = choice(amount_rows[random_contact])
                        random_row["amount"] = Decimal(
                            random_row["amount"] + difference
                        ).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
                    else:
                        # Somehow there was no suitable rent share. Add
                        # The amount to a random tenant
                        # TODO: Should do something else?
                        random_contact = choice(list(shares.keys()))
                        random_tenant = choice(list(shares[random_contact].keys()))
                        rounded_amount = Decimal(calculation_amount.amount).quantize(
                            Decimal(".01"), rounding=ROUND_HALF_UP
                        )

                        amount_rows[random_contact].append(
                            {
                                "tenant": random_tenant,
                                "receivable_type": receivable_type_rent,
                                "intended_use": calculation_amount.item.intended_use,
                                "billing_period_start_date": amount_period[0],
                                "billing_period_end_date": amount_period[1],
                                "amount": rounded_amount,
                            }
                        )

                for contact, rows in amount_rows.items():
                    contact_rows[contact].extend(rows)

            # TODO: If there are no suitable contacts for some time periods, add
            #  the remaining amounts to someone
            total_period_amount = sum(
                [row["amount"] for rows in contact_rows.values() for row in rows]
            )
            total_period_amount = Decimal(total_period_amount).quantize(
                Decimal(".01"), rounding=ROUND_HALF_UP
            )

            billing_period_invoices = []
            for contact, rows in contact_rows.items():
                notes = [
                    note.notes
                    for note in self.invoice_notes.filter(
                        billing_period_start_date=billing_period[0],
                        billing_period_end_date=billing_period[1],
                        notes__isnull=False,
                    )
                ]

                billable_amount = sum([row["amount"] for row in rows])
                billable_amount = Decimal(billable_amount).quantize(
                    Decimal(".01"), rounding=ROUND_HALF_UP
                )

                invoice_datum = {
                    "type": InvoiceType.CHARGE,
                    "lease": self,
                    "recipient": contact,
                    "due_date": period_rent["due_date"],
                    "billing_period_start_date": billing_period[0],
                    "billing_period_end_date": billing_period[1],
                    "total_amount": total_period_amount,
                    "billed_amount": billable_amount,
                    "rows": rows,
                    "explanations": [
                        period_rent["calculation_result"].get_explanation()
                    ],
                    "calculation_result": period_rent["calculation_result"],
                    "state": InvoiceState.OPEN,
                    "notes": " ".join(notes),
                }

                billing_period_invoices.append(invoice_datum)

            invoice_data.append(billing_period_invoices)

        # Add the cent amounts to the invoice_data that are missing
        # due to roundings during the year.
        if last_billing_period:
            self._year_rent_rounding_correction(
                last_billing_period, invoice_data, dry_run=dry_run
            )

        return invoice_data

    def _year_rent_rounding_correction(  # noqa C901 TODO
        self, last_billing_period, invoice_data, dry_run=False
    ):
        round_adjust_year = last_billing_period[0].year
        first_day_of_year = datetime.date(year=round_adjust_year, month=1, day=1)
        last_day_of_year = datetime.date(year=round_adjust_year, month=12, day=31)

        # Gather all billing periods there are for all of the rents
        billing_periods = set()
        for rent in self.get_active_rents_on_period(
            first_day_of_year, last_day_of_year
        ):
            billing_periods.update(
                rent.get_all_billing_periods_for_year(round_adjust_year)
            )

        # Calculate what the already billed amount is
        already_billed_amounts = defaultdict(Decimal)
        for billing_period in billing_periods:
            # First try to find the billing period invoice from the invoices
            # currently being created.
            found = False
            for period_invoice_data in invoice_data:
                for datum in period_invoice_data:
                    if (
                        datum["billing_period_start_date"] == billing_period[0]
                        and datum["billing_period_end_date"] == billing_period[1]
                    ):
                        for row in datum["rows"]:
                            already_billed_amounts[row["intended_use"]] += row["amount"]
                        found = True

            # If not found, calculate from the previously generated invoices
            if not found:
                for row in InvoiceRow.objects.filter(
                    intended_use__isnull=False,
                    invoice__lease=self,
                    invoice__billing_period_start_date=billing_period[0],
                    invoice__billing_period_end_date=billing_period[1],
                    invoice__generated=True,
                    invoice__deleted__isnull=True,
                ):
                    already_billed_amounts[row.intended_use] += row.amount

        total_amounts_for_year = self.calculate_rent_amount_for_year(
            round_adjust_year, dry_run=dry_run
        ).get_total_amounts_by_intended_uses()

        difference_by_intended_use = {}

        for intended_use, already_billed_amount in already_billed_amounts.items():
            if intended_use not in total_amounts_for_year:
                continue

            already_billed_amount = Decimal(already_billed_amount).quantize(
                Decimal(".01"), rounding=ROUND_HALF_UP
            )
            total_amount_for_year = Decimal(
                total_amounts_for_year[intended_use]
            ).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)

            # Check for rounding errors
            difference = total_amount_for_year - already_billed_amount

            # Limit rounding to maximum of Decimal(1) because cancelled
            # or manually added invoices could affect the calculation.
            if not difference or difference.copy_abs() > Decimal(1):
                continue

            difference_by_intended_use[intended_use] = difference

        if not difference_by_intended_use:
            return

        # Distribute the differences to the tenants according to their rent
        # share by using calculate_invoices method again. Rounding error
        # correction won't happen again because last_billing_period is set
        # to False.
        rounding_calculation_result = CalculationResult(
            date_range_start=last_billing_period[0],
            date_range_end=last_billing_period[1],
        )

        class BogusItem:
            def __init__(self, intended_use):
                self.intended_use = intended_use

        for intended_use, amount in difference_by_intended_use.items():
            rounding_calculation_result.add_amount(
                CalculationAmount(
                    BogusItem(intended_use),
                    last_billing_period[0],
                    last_billing_period[1],
                    amount,
                )
            )

        rounding_amounts = {
            last_billing_period: {
                "due_date": None,
                "calculation_result": rounding_calculation_result,
                "last_billing_period": False,
            }
        }

        rounding_invoice_data = self.calculate_invoices(rounding_amounts)

        # Inject the rounding rows to the invoices
        for rounding_invoice_datum in rounding_invoice_data[0]:
            for period_invoices in invoice_data:
                injected = False
                for invoice_datum in period_invoices:
                    if (
                        invoice_datum["billing_period_start_date"]
                        == last_billing_period[0]
                        and invoice_datum["billing_period_end_date"]
                        == last_billing_period[1]
                        and invoice_datum["recipient"]
                        == rounding_invoice_datum["recipient"]
                    ):
                        invoice_datum["rows"].extend(rounding_invoice_datum["rows"])
                        invoice_datum["billed_amount"] = sum(
                            [row["amount"] for row in invoice_datum["rows"]]
                        )
                        injected = True

                if not injected:
                    continue

                # Adjust total_amount in the affected invoice sets
                total_period_amount = sum(
                    [
                        row["amount"]
                        for period_invoice in period_invoices
                        for row in period_invoice["rows"]
                    ]
                )
                for period_invoice in period_invoices:
                    period_invoice["total_amount"] = total_period_amount

    def generate_first_invoices(self, end_date=None):  # noqa C901 TODO
        from leasing.models.invoice import Invoice, InvoiceRow, InvoiceSet

        today = datetime.date.today()

        if not self.start_date:
            # TODO: Emit error
            return []

        if not end_date:
            end_date = (
                today if not self.end_date or self.end_date >= today else self.end_date
            )

        years = range(self.start_date.year, end_date.year + 1)

        if not years:
            return []

        # Calculate amounts for all the billing periods that have
        # occurred before the next possible invoicing day.
        amounts_for_billing_periods = self.determine_payable_rents_and_periods(
            datetime.date(year=min(years), month=1, day=1),
            datetime.date(year=max(years) + 1, month=1, day=31),
            dry_run=False,
            ignore_invoicing_date_after=end_date,
        )

        # Nothing to invoice
        if not amounts_for_billing_periods:
            return []

        invoice_data = self.calculate_invoices(amounts_for_billing_periods)

        # Flatten and sort the data
        invoice_data = sorted(chain(*invoice_data), key=lambda x: x.get("recipient").id)

        # Calculate total and determine the longest billing period
        total_total_amount = Decimal(0)
        recipients = set()
        billing_period_start_date = datetime.date(year=2500, day=1, month=1)
        billing_period_end_date = datetime.date(year=2000, day=1, month=1)
        for invoice_datum in invoice_data:
            total_total_amount += invoice_datum["billed_amount"]
            recipients.add(invoice_datum["recipient"])
            billing_period_start_date = min(
                invoice_datum["billing_period_start_date"], billing_period_start_date
            )
            billing_period_end_date = max(
                invoice_datum["billing_period_end_date"], billing_period_end_date
            )

        new_due_date = today + relativedelta(days=settings.MVJ_DUE_DATE_OFFSET_DAYS)

        invoiceset = None
        if len(recipients) > 1:
            try:
                invoiceset = InvoiceSet.objects.get(
                    lease=self,
                    billing_period_start_date=billing_period_start_date,
                    billing_period_end_date=billing_period_end_date,
                )
            except InvoiceSet.DoesNotExist:
                invoiceset = InvoiceSet.objects.create(
                    lease=self,
                    billing_period_start_date=billing_period_start_date,
                    billing_period_end_date=billing_period_end_date,
                )

        # Group by recipient and generate merged invoices
        invoices = []
        for recipient, recipient_invoice_data in groupby(
            invoice_data, key=lambda x: x.get("recipient")
        ):
            total_billed_amount = Decimal(0)
            billing_period_start_date = datetime.date(year=2500, day=1, month=1)
            billing_period_end_date = datetime.date(year=2000, day=1, month=1)
            rows = []

            for recipient_invoice_datum in recipient_invoice_data:
                billing_period_start_date = min(
                    recipient_invoice_datum["billing_period_start_date"],
                    billing_period_start_date,
                )
                billing_period_end_date = max(
                    recipient_invoice_datum["billing_period_end_date"],
                    billing_period_end_date,
                )
                total_billed_amount += recipient_invoice_datum["billed_amount"]
                rows.extend(recipient_invoice_datum["rows"])

            invoice_data = {
                "lease": self,
                "invoicing_date": today,
                "billing_period_start_date": billing_period_start_date,
                "billing_period_end_date": billing_period_end_date,
                "billed_amount": total_billed_amount,
                "outstanding_amount": total_billed_amount,
                "total_amount": total_total_amount,
                "state": InvoiceState.OPEN,
                "type": InvoiceType.CHARGE,
                "due_date": new_due_date,
                "recipient": recipient,
                "invoiceset": invoiceset,
                "generated": True,
            }

            try:
                invoice = Invoice.objects.get(**invoice_data)
            except Invoice.DoesNotExist:
                invoice = Invoice.objects.create(**invoice_data)

                for row in rows:
                    row["invoice"] = invoice
                    InvoiceRow.objects.create(**row)

            invoices.append(invoice)

        return invoices

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

    def is_empty(self):
        skip_fields = (
            "id",
            "type",
            "municipality",
            "district",
            "identifier",
            "state",
            "preparer",
            "note",
            "created_at",
            "modified_at",
            "plot_search_target",
        )

        return is_instance_empty(self, skip_fields=skip_fields)


class LeaseStateLog(TimeStampedModel):
    lease = models.ForeignKey(Lease, verbose_name=_("Lease"), on_delete=models.PROTECT)
    state = EnumField(LeaseState, verbose_name=_("State"), max_length=30)

    recursive_get_related_skip_relations = ["lease"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Lease state log")
        verbose_name_plural = pgettext_lazy("Model name", "Lease state logs")


class RelatedLease(TimeStampedSafeDeleteModel):
    from_lease = models.ForeignKey(
        Lease,
        verbose_name=_("From lease"),
        related_name="from_leases",
        on_delete=models.PROTECT,
    )
    to_lease = models.ForeignKey(
        Lease,
        verbose_name=_("To lease"),
        related_name="to_leases",
        on_delete=models.PROTECT,
    )
    type = EnumField(
        LeaseRelationType,
        verbose_name=_("Lease relation type"),
        null=True,
        blank=True,
        max_length=30,
    )
    start_date = models.DateField(verbose_name=_("Start date"), null=True, blank=True)
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    recursive_get_related_skip_relations = ["from_lease", "to_lease"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Related lease")
        verbose_name_plural = pgettext_lazy("Model name", "Related leases")


auditlog.register(Lease)
auditlog.register(RelatedLease)

field_permissions.register(
    Lease,
    exclude_fields=[
        "from_leases",
        "to_leases",
        "leases",
        "invoicesets",
        "leasestatelog",
    ],
)
