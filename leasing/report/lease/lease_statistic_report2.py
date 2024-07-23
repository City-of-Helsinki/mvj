import datetime
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from django import forms
from django.db.models import Q
from django.utils import formats
from django.utils.translation import gettext_lazy as _
from enumfields.drf import EnumField

from leasing.enums import LeaseState, SubventionType
from leasing.models import Lease, ServiceUnit
from leasing.report.lease.common_getters import (
    get_address,
    get_contract_number,
    get_district,
    get_form_of_management,
    get_form_of_regulation,
    get_lease_area_identifier,
    get_lease_id,
    get_lease_type,
    get_lessor,
    get_notice_period,
    get_option_to_purchase,
    get_preparer,
    get_re_lease,
    get_supportive_housing,
    get_tenants,
    get_total_area,
)
from leasing.report.report_base import AsyncReportBase


def get_latest_decision_maker(lease):
    decision_makers = []

    for decision in lease.decisions.all():
        decision_makers.append(
            (
                decision.decision_maker.name if decision.decision_maker else "",
                decision.decision_date,
            )
        )
    decision_makers.sort(key=lambda x: x[1] if x[1] else datetime.date.today())

    if len(decision_makers) > 0:
        latest_decision_maker = decision_makers[-1]
        return "{} ({})".format(latest_decision_maker[0], latest_decision_maker[1])
    else:
        return ""


def get_form_of_financing(lease):
    if not lease.financing:
        return
    return lease.financing.name


def get_amount_per_area_index_adjusted(obj):
    volumes = defaultdict(Decimal)

    for basis_of_rent in obj.basis_of_rents.all():
        if (
            not basis_of_rent.amount_per_area
            or basis_of_rent.archived_at
            or not basis_of_rent.locked_at
        ):
            continue

        if basis_of_rent.index:
            index_ratio = Decimal(basis_of_rent.index.number / 100)
        else:
            index_ratio = Decimal(1)

        volumes[basis_of_rent.area_unit] += basis_of_rent.amount_per_area * index_ratio

    return ", ".join(
        [
            "{} € / {}".format(
                formats.number_format(
                    amounts_per_area.quantize(Decimal(".01"), rounding=ROUND_HALF_UP),
                    decimal_pos=2,
                    use_l10n=True,
                ),
                area_unit,
            )
            for area_unit, amounts_per_area in volumes.items()
        ]
    )


def get_initial_year_rent(lease):
    amount = Decimal(0)
    for basis_of_rent in lease.basis_of_rents.all():
        if basis_of_rent.archived_at or not basis_of_rent.locked_at:
            continue

        amount += basis_of_rent.calculate_initial_year_rent()

    return amount.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)


def get_subsidised_rent(lease):
    subsidy_amount = Decimal(0)
    initial_year_rent = Decimal(0)
    for basis_of_rent in lease.basis_of_rents.all():
        if basis_of_rent.archived_at or not basis_of_rent.locked_at:
            continue

        initial_year_rent += basis_of_rent.calculate_initial_year_rent()
        subsidy_amount += basis_of_rent.calculate_subsidy()

    return (initial_year_rent - subsidy_amount).quantize(
        Decimal(".01"), rounding=ROUND_HALF_UP
    )


def get_subsidy_amount(lease):
    subsidy_amount = Decimal(0)
    for basis_of_rent in lease.basis_of_rents.all():
        if basis_of_rent.archived_at or not basis_of_rent.locked_at:
            continue

        subsidy_amount += basis_of_rent.calculate_subsidy()

    return subsidy_amount.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)


def get_subsidy_percent(lease):
    subsidy_amount = Decimal(0)
    initial_year_rent = Decimal(0)
    for basis_of_rent in lease.basis_of_rents.all():
        if basis_of_rent.archived_at:
            continue

        initial_year_rent += basis_of_rent.calculate_initial_year_rent()
        subsidy_amount += basis_of_rent.calculate_subsidy()

    if (
        subsidy_amount.compare(Decimal(0)) == 0
        or initial_year_rent.compare(Decimal(0)) == 0
    ):
        return Decimal(0)

    return (subsidy_amount * 100 / initial_year_rent).quantize(
        Decimal(".01"), rounding=ROUND_HALF_UP
    )


def get_subsidy_amount_per_area(lease):
    rent_per_area_index_adjusted = Decimal(0)
    subsidy_amount = Decimal(0)
    for basis_of_rent in lease.basis_of_rents.all():
        if (
            basis_of_rent.archived_at
            or not basis_of_rent.amount_per_area
            or not basis_of_rent.locked_at
        ):
            continue

        if basis_of_rent.index:
            index_ratio = Decimal(basis_of_rent.index.number / 100)
        else:
            index_ratio = Decimal(1)

        rent_per_area_index_adjusted += basis_of_rent.amount_per_area * index_ratio

        if basis_of_rent.subvention_type == SubventionType.FORM_OF_MANAGEMENT:
            management_subventions = basis_of_rent.management_subventions.all()
            if management_subventions:
                for management_subvention in management_subventions:
                    subsidy_amount += management_subvention.subvention_amount
        elif basis_of_rent.subvention_type == SubventionType.RE_LEASE:
            base_percent = (
                basis_of_rent.subvention_base_percent
                if basis_of_rent.subvention_base_percent
                else 0
            )
            graduated_percent = (
                basis_of_rent.subvention_graduated_percent
                if basis_of_rent.subvention_graduated_percent
                else 0
            )
            subvention_percent = (
                1
                - Decimal(1 - base_percent / 100) * Decimal(1 - graduated_percent / 100)
            ) * 100
            subsidy_amount = rent_per_area_index_adjusted * (
                1 - (subvention_percent / 100)
            )

    if not subsidy_amount:
        return Decimal(0)

    return (subsidy_amount - rent_per_area_index_adjusted).quantize(
        Decimal(".01"), rounding=ROUND_HALF_UP
    )


def get_temporary_discount_percentage(lease):
    base = Decimal(1)
    for basis_of_rent in lease.basis_of_rents.all():
        if basis_of_rent.archived_at or not basis_of_rent.locked_at:
            continue

        temporary_subventions = basis_of_rent.temporary_subventions.all()
        if not temporary_subventions:
            continue

        for temporary_subvention in temporary_subventions:
            base *= (100 - temporary_subvention.subvention_percent) / 100

    return (1 - base) * 100


def get_temporary_discount_amount(lease):
    temporary_discount_percentage = get_temporary_discount_percentage(lease)
    subsidised_rent = get_subsidised_rent(lease)

    return (subsidised_rent / 100 * temporary_discount_percentage).quantize(
        Decimal(".01"), rounding=ROUND_HALF_UP
    )


def get_subvention_form_of_management(lease):
    forms_of_management = []
    for rent in lease.rents.all():
        for rent_adjustment in rent.rent_adjustments.all():
            for management_subvention in rent_adjustment.management_subventions.all():
                if not management_subvention.management:
                    continue
                forms_of_management.append(management_subvention.management.name)

    return ", ".join(forms_of_management)


class LeaseStatisticReport2(AsyncReportBase):
    name = _("Lease statistics report II")
    description = _("Shows statistics about leases and their basis of rents")
    slug = "lease_statistic2"
    input_fields = {
        "service_unit": forms.ModelMultipleChoiceField(
            label=_("Service unit"),
            queryset=ServiceUnit.objects.all(),
            required=False,
        ),
        "start_date": forms.DateField(label=_("Start date"), required=False),
        "state": forms.ChoiceField(
            label=_("State"), required=False, choices=LeaseState.choices()
        ),
        "only_active_leases": forms.BooleanField(
            label=_("Only active leases"), required=False
        ),
    }
    output_fields = {
        "lease_id": {"label": _("Lease id"), "source": get_lease_id},
        # Sopimusnumero
        "contract_number": {
            "label": _("Contract number"),
            "source": get_contract_number,
            "is_numeric": True,
        },
        # Vuokrauksen laji
        "type": {"label": _("Lease type"), "source": get_lease_type, "width": 5},
        # Vuokrauksen tila
        "state": {
            "label": _("Lease state"),
            "serializer_field": EnumField(enum=LeaseState),
            "width": 20,
        },
        # Valmistelija
        "preparer": {"label": _("Preparer"), "source": get_preparer, "width": 20},
        # Kaupunginosa
        "district": {"label": _("District"), "source": get_district, "width": 20},
        # Kohteen tunnus
        "lease_area_identifier": {
            "label": _("Lease area identifier"),
            "source": get_lease_area_identifier,
            "width": 20,
        },
        # Osoite
        "address": {"label": _("Address"), "source": get_address, "width": 30},
        # Vuokranantaja
        "lessor": {"label": _("Lessor"), "source": get_lessor, "width": 30},
        # Rakennuttaja
        "real_estate_developer": {"label": _("Real estate developer"), "width": 20},
        # Vuokralaiset
        "tenants": {
            "label": _("Tenants"),
            "source": lambda x: get_tenants(x, include_future_tenants=True),
            "width": 40,
        },
        # Päättäjä
        "decision_maker": {
            "label": _("Decision maker"),
            "source": get_latest_decision_maker,
            "width": 20,
        },
        # Start date
        "start_date": {"label": _("Start date"), "format": "date"},
        # End date
        "end_date": {"label": _("End date"), "format": "date"},
        # Kokonaispinta-ala
        "total_area": {
            "label": _("Total area"),
            "source": get_total_area,
            "format": "area",
        },
        # Yksikköhinta (ind)
        "amount_per_area_index_adjusted": {
            "label": _("Unit price (index)"),
            "source": get_amount_per_area_index_adjusted,
            "width": 20,
        },
        # Alkuvuosivuokra (ind)
        "initial_year_rent": {
            "label": _("Initial year rent"),
            "source": get_initial_year_rent,
            "format": "money",
            "width": 13,
        },
        # Subventoitu Alkuvuosivuokra (ind)
        "subsidised_rent": {
            "label": _("Subsidised rent"),
            "source": get_subsidised_rent,
            "format": "money",
            "width": 13,
        },
        # Hallintamuoto
        "form_of_management": {
            "label": _("Form of management"),
            "source": get_form_of_management,
            "width": 13,
        },
        # Rahoitusmuoto (yhteenvedon tilastotiedoista)
        "financing": {
            "label": _("Form of financing"),
            "source": get_form_of_financing,
            "width": 20,
        },
        # Erityisasunnot
        "supportive_housing": {
            "label": _("Supportive housing"),
            "source": get_supportive_housing,
            "width": 13,
        },
        # Sääntelymuoto
        "form_of_regulation": {
            "label": _("Form of regulation"),
            "source": get_form_of_regulation,
            "width": 20,
        },
        # Uudelleenvuokraus
        "re_lease": {
            "label": _("Re-lease"),
            "source": get_re_lease,
            "format": "boolean",
        },
        # Osto-oikeus
        "option_to_purchase": {
            "label": _("Option to purchase"),
            "source": get_option_to_purchase,
            "format": "boolean",
        },
        # Subventio euroina/vuosi (laskurista)
        "subsidy_amount": {
            "label": _("Subsidy amount"),
            "source": get_subsidy_amount,
            "format": "money",
            "width": 13,
        },
        # Subventio prosentteina (laskurista)
        "subsidy_percent": {
            "label": _("Subsidy percent"),
            "source": get_subsidy_percent,
            "format": "percentage",
            "width": 13,
        },
        # Subventoitu eur/k-m2 = Subventoitu yksikköhinta - Yksikköhinta (ind)
        "subsidy_amount_per_area": {
            "label": _("Subsidy amount per area"),
            "source": get_subsidy_amount_per_area,
            "format": "money",
            "width": 13,
        },
        # Tilapäisalennus subventoidusta alkuvuosivuokrasta % (laskurista)
        "temporary_discount_percentage": {
            "label": _("Temporary discount percent"),
            "source": get_temporary_discount_percentage,
            "format": "percentage",
            "width": 13,
        },
        # Tilapäisalennus euroa/vuosi (laskurista)
        "temporary_discount_amount": {
            "label": _("Temporary discount amount"),
            "source": get_temporary_discount_amount,
            "format": "money",
            "width": 13,
        },
        # Hallintamuodon tyyppi (Subventio)
        "subvention_form_of_management": {
            "label": _("Form of management (Subvention)"),
            "source": get_subvention_form_of_management,
            "width": 20,
        },
        # Irtisanomisaika
        "notice_period": {
            "label": _("Notice period"),
            "source": get_notice_period,
            "width": 20,
        },
    }
    async_task_timeout = 60 * 30  # 30 minutes

    def get_data(self, input_data):
        qs = Lease.objects.select_related(
            "identifier__type",
            "identifier__district",
            "identifier__municipality",
            "lessor",
            "preparer",
            "management",
            "district",
            "supportive_housing",
            "financing",
            "type",
            "notice_period",
            "regulation",
        ).prefetch_related(
            "rents",
            "rents__rent_adjustments",
            "rents__rent_adjustments__management_subventions",
            "contracts",
            "lease_areas",
            "lease_areas__addresses",
            "lease_areas__attachments",
            "decisions",
            "decisions__decision_maker",
            "decisions__conditions",
            "tenants",
            "tenants__tenantcontact_set",
            "tenants__tenantcontact_set__contact",
            "basis_of_rents",
            "basis_of_rents__index",
            "basis_of_rents__management_subventions",
            "basis_of_rents__temporary_subventions",
        )

        if input_data["service_unit"]:
            qs = qs.filter(service_unit__in=input_data["service_unit"])

        if input_data["start_date"]:
            qs = qs.filter(start_date__gte=input_data["start_date"])

        if input_data["state"]:
            qs = qs.filter(state=input_data["state"])

        if input_data["only_active_leases"]:
            qs = qs.filter(
                Q(end_date__isnull=True) | Q(end_date__gte=datetime.date.today())
            )

        return qs

    def generate_report(self, user, input_data):
        report_data = self.get_data(input_data)
        serialized_report_data = self.serialize_data(report_data)

        return self.data_as_excel(serialized_report_data)
