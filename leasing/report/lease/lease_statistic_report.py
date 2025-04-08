import datetime
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache
from io import BytesIO
from typing import Any, Type, TypedDict

import xlsxwriter
from django import forms
from django.db.models import Q, QuerySet
from django.utils import formats
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django_q.conf import Conf
from django_q.tasks import async_task
from enumfields.drf import EnumField
from rest_framework.request import Request
from rest_framework.response import Response

from leasing.enums import AreaUnit, LeaseAreaAttachmentType, LeaseState, SubventionType
from leasing.models import Lease, ServiceUnit
from leasing.report.excel import ExcelRow, FormatType
from leasing.report.lease.common_getters import (
    get_address,
    get_district,
    get_form_of_management,
    get_form_of_regulation,
    get_identifier_string_from_lease_link_data,
    get_latest_contract_number,
    get_lease_area_identifier,
    get_lease_identifier_string,
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
from leasing.report.report_base import (
    AsyncReportBase,
    send_email_report,
)

# TODO: Can we get rid of static ids
RESIDENTIAL_INTENDED_USE_IDS = [
    1,
    12,
    13,
]  # 1 = Asunto, 12 = Asunto, lisärakent., 13 = Asunto 2


class LeaseStatisticReportInputData(TypedDict):
    service_unit: list[int] | None
    start_date: datetime.date | None
    only_active_leases: bool | None
    state: str | None


LeaseBasisOfRentRowLabels = [
    gettext("Lease identifier"),
    gettext("Type"),
    gettext("Intended use"),
    gettext("Index"),
    gettext("Area"),  # TODO: Add translation
    gettext("Area unit"),
    gettext("Amount per area"),  # TODO: Add translation
    gettext("Profit margin percentage"),
    gettext("Initial year rent"),
    gettext("Subvention type"),
    gettext("Subvented initial year rent"),  # TODO: Add translation
    gettext("Subvention euros / year"),
    gettext("Subvention percent"),
    gettext("Subvention amount per area"),  # TODO: Add translation
    gettext(
        "Subvention base percent"
    ),  # TODO: Perusalennus markkinavuokrasta? Is this correct?
    gettext("Subvention graduated percent"),  # TODO: Add translation
    gettext("Temporary discount percentage"),  # TODO: Add translation
    gettext("Temporary discount amount euros per year"),  # TODO: Add translation
]


def get_latest_decision(lease):
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


def get_matti_report(obj):
    for lease_area in obj.lease_areas.all():
        if lease_area.archived_at:
            continue

        for attachment in lease_area.attachments.all():
            if attachment.type == LeaseAreaAttachmentType.MATTI_REPORT:
                return True

    return False


def get_permitted_building_volume_residential(obj):
    volumes = defaultdict(Decimal)
    for basis_of_rent in obj.basis_of_rents.all():
        if (
            basis_of_rent.intended_use_id not in RESIDENTIAL_INTENDED_USE_IDS
            or basis_of_rent.archived_at
            or not basis_of_rent.locked_at
        ):
            continue

        volumes[basis_of_rent.area_unit] += basis_of_rent.area

    return " / ".join(
        [
            "{} {}".format(
                formats.number_format(area, decimal_pos=2, use_l10n=True), area_unit
            )
            for area_unit, area in volumes.items()
        ]
    )


def get_permitted_building_volume_business(obj):
    volumes = defaultdict(Decimal)
    for basis_of_rent in obj.basis_of_rents.all():
        if (
            basis_of_rent.intended_use_id in RESIDENTIAL_INTENDED_USE_IDS
            or basis_of_rent.archived_at
            or not basis_of_rent.locked_at
        ):
            continue

        volumes[basis_of_rent.area_unit] += basis_of_rent.area

    return " / ".join(
        [
            "{} {}".format(
                formats.number_format(area, decimal_pos=2, use_l10n=True), area_unit
            )
            for area_unit, area in volumes.items()
        ]
    )


def get_permitted_building_volume_total(obj):
    volumes = defaultdict(Decimal)
    for basis_of_rent in obj.basis_of_rents.all():
        if basis_of_rent.archived_at or not basis_of_rent.locked_at:
            continue

        volumes[basis_of_rent.area_unit] += basis_of_rent.area

    return " / ".join(
        [
            "{} {}".format(
                formats.number_format(area, decimal_pos=2, use_l10n=True), area_unit
            )
            for area_unit, area in volumes.items()
        ]
    )


@lru_cache(maxsize=1)
def _get_rent_amount_for_year(lease: Lease, year):
    return lease.calculate_rent_amount_for_year(year, dry_run=True)


def get_rent_amount_residential(obj):
    year = datetime.date.today().year
    total_amount = Decimal(0)
    for intended_use, amount in (
        _get_rent_amount_for_year(obj, year)
        .get_total_amounts_by_intended_uses()
        .items()
    ):
        if intended_use.id in RESIDENTIAL_INTENDED_USE_IDS:
            total_amount += amount

    return total_amount


def get_rent_amount_business(obj):
    year = datetime.date.today().year
    total_amount = Decimal(0)
    for intended_use, amount in (
        _get_rent_amount_for_year(obj, year)
        .get_total_amounts_by_intended_uses()
        .items()
    ):
        if intended_use.id not in RESIDENTIAL_INTENDED_USE_IDS:
            total_amount += amount

    return total_amount


def get_total_rent_amount_for_year(obj):
    year = datetime.date.today().year
    return _get_rent_amount_for_year(obj, year).get_total_amount()


def get_average_amount_per_area_residential(obj):
    volumes = defaultdict(list)
    for basis_of_rent in obj.basis_of_rents.all():
        if (
            basis_of_rent.intended_use_id not in RESIDENTIAL_INTENDED_USE_IDS
            or not basis_of_rent.amount_per_area
            or basis_of_rent.archived_at
            or not basis_of_rent.locked_at
        ):
            continue

        volumes[basis_of_rent.area_unit].append(basis_of_rent.amount_per_area)

    return " / ".join(
        [
            "{} {}".format(
                formats.number_format(
                    sum(amounts_per_area) / len(amounts_per_area),
                    decimal_pos=2,
                    use_l10n=True,
                ),
                area_unit,
            )
            for area_unit, amounts_per_area in volumes.items()
        ]
    )


def get_average_amount_per_area_business(obj):
    volumes = defaultdict(list)
    for basis_of_rent in obj.basis_of_rents.all():
        if (
            basis_of_rent.intended_use_id in RESIDENTIAL_INTENDED_USE_IDS
            or not basis_of_rent.amount_per_area
            or basis_of_rent.archived_at
            or not basis_of_rent.locked_at
        ):
            continue

        volumes[basis_of_rent.area_unit].append(basis_of_rent.amount_per_area)

    return " / ".join(
        [
            "{} {}".format(
                formats.number_format(
                    sum(amounts_per_area) / len(amounts_per_area),
                    decimal_pos=2,
                    use_l10n=True,
                ),
                area_unit,
            )
            for area_unit, amounts_per_area in volumes.items()
        ]
    )


def get_amount_per_area_index_adjusted(lease):
    volumes = defaultdict(Decimal)

    for basis_of_rent in lease.basis_of_rents.filter(
        archived_at__isnull=True, locked_at__isnull=False, amount_per_area__isnull=False
    ):
        volumes[
            basis_of_rent.area_unit
        ] += basis_of_rent.get_index_adjusted_amount_per_area()

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
    for basis_of_rent in lease.basis_of_rents.filter(
        archived_at__isnull=True, locked_at__isnull=False
    ):
        amount += basis_of_rent.calculate_initial_year_rent()

    return amount.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)


def get_subvented_initial_year_rent(lease):
    subvented_rent_total = Decimal(0)
    for basis_of_rent in lease.basis_of_rents.filter(
        archived_at__isnull=True, locked_at__isnull=False
    ):
        subvented_rent_total += basis_of_rent.calculate_subvented_initial_year_rent()

    return subvented_rent_total.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)


def get_subvention_euros_per_year(lease):
    initial_year_rent_total = Decimal(0)
    subvented_initial_year_rent_total = Decimal(0)
    for basis_of_rent in lease.basis_of_rents.filter(
        archived_at__isnull=True, locked_at__isnull=False
    ):
        initial_year_rent_total += basis_of_rent.calculate_initial_year_rent()
        subvented_initial_year_rent_total += (
            basis_of_rent.calculate_subvented_initial_year_rent()
        )

    return (initial_year_rent_total - subvented_initial_year_rent_total).quantize(
        Decimal(".001"), rounding=ROUND_HALF_UP
    )


def get_subsidy_percent(lease):
    subvention_amount = Decimal(0)
    initial_year_rent = Decimal(0)
    for basis_of_rent in lease.basis_of_rents.filter(
        archived_at__isnull=True, locked_at__isnull=False
    ):
        initial_year_rent += basis_of_rent.calculate_initial_year_rent()
        subvention_amount += basis_of_rent.calculate_subvention_amount()

    if (
        subvention_amount.compare(Decimal(0)) == 0
        or initial_year_rent.compare(Decimal(0)) == 0
    ):
        return Decimal(0)

    return (subvention_amount * 100 / initial_year_rent).quantize(
        Decimal(".01"), rounding=ROUND_HALF_UP
    )


def get_subsidy_amount_per_area(lease):
    rent_per_area_index_adjusted = Decimal(0)
    subsidy_amount = Decimal(0)
    for basis_of_rent in lease.basis_of_rents.filter(
        archived_at__isnull=True, locked_at__isnull=False, amount_per_area__isnull=False
    ):
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
    for basis_of_rent in lease.basis_of_rents.filter(
        archived_at__isnull=True, locked_at__isnull=False
    ):
        temporary_subventions = basis_of_rent.temporary_subventions.all()
        if not temporary_subventions:
            continue

        for temporary_subvention in temporary_subventions:
            base *= (100 - temporary_subvention.subvention_percent) / 100

    return (1 - base) * 100


def get_temporary_discount_amount_euros_per_year(lease):
    temporary_discount_amount_total = Decimal(0)

    for basis_of_rent in lease.basis_of_rents.filter(
        archived_at__isnull=True, locked_at__isnull=False
    ):
        cumulative_temporary_subventions = (
            basis_of_rent.calculate_cumulative_temporary_subventions()
        )
        for subvention in cumulative_temporary_subventions:
            temporary_discount_amount_total += subvention[
                "subvention_amount_euros_per_year"
            ]

    return (temporary_discount_amount_total).quantize(
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


def get_form_of_financing(lease):
    if not lease.financing:
        return
    return lease.financing.name


class LeaseStatisticReport(AsyncReportBase):
    name = _("Lease statistics report")
    description = _(
        "Shows information about all leases or if start date is provided the leases that have started on or after it"
    )
    slug = "lease_statistic"
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
        "lease_id": {"label": _("Lease id"), "source": get_lease_identifier_string},
        # Sopimusnumero
        "contract_number": {
            "label": _("Contract number"),
            "source": get_latest_contract_number,
            "is_numeric": True,
        },
        # Vuokrauksen tyyppi
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
        "address": {"label": _("Address"), "source": get_address, "width": 20},
        # Vuokranantaja
        "lessor": {"label": _("Lessor"), "source": get_lessor, "width": 30},
        # Rakennuttaja
        "real_estate_developer": {"label": _("Real estate developer"), "width": 20},
        # Vuokralaiset
        "tenants": {
            "label": _("Tenants"),
            "source": lambda x: get_tenants(
                x, include_future_tenants=False, report="Lease statistics report"
            ),
            "width": 40,
        },
        # Viimeisin päätös
        "decision_maker": {
            "label": _("Latest decision"),
            "source": get_latest_decision,
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
        # Rakennus-oikeus (asuminen)
        "permitted_building_volume_residential": {
            "label": _("Permitted building volume (Residential)"),
            "source": get_permitted_building_volume_residential,
            "width": 20,
        },
        # Vuosivuokra (asuminen)
        "rent_amount_residential": {
            "label": _("Rent amount (Residential)"),
            "source": get_rent_amount_residential,
            "format": "money",
            "width": 13,
        },
        # Rakennusoikeus (yritystila)
        "get_permitted_building_volume_business": {
            "label": _("Permitted building volume (Business)"),
            "source": get_permitted_building_volume_business,
            "width": 20,
        },
        # Vuosivuokra (yritystila)
        "rent_amount_business": {
            "label": _("Rent amount (Business)"),
            "source": get_rent_amount_business,
            "format": "money",
            "width": 13,
        },
        # Kokonaisrakennusoikeus
        "get_permitted_building_volume_total": {
            "label": _("Permitted building volume total"),
            "source": get_permitted_building_volume_total,
            "width": 20,
        },
        # Vuosivuokra yhteensä
        "total_rent_amount_for_year": {
            "label": _("Total rent amount for year"),
            "source": get_total_rent_amount_for_year,
            "format": "money",
            "width": 13,
        },
        # €/k-m2 Asuminen
        "average_amount_per_area_residential": {
            "label": _("Average amount per area (Residential)"),
            "source": get_average_amount_per_area_residential,
            "width": 20,
        },
        # €/k-m2 Yritystila
        "get_average_amount_per_area_business": {
            "label": _("Average amount per area (Business)"),
            "source": get_average_amount_per_area_business,
            "width": 20,
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
            "label": _("Subsidised initial year rent"),
            "source": get_subvented_initial_year_rent,
            "format": "money",
            "width": 13,
        },
        # Subventio euroina / vuosi (laskurista)
        "subvention_euros_per_year": {
            "label": _("Subvention euros / year"),
            "source": get_subvention_euros_per_year,
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
        "temporary_discount_amount_euros_per_year": {
            "label": _("Temporary discount amount euros / year"),
            "source": get_temporary_discount_amount_euros_per_year,
            "format": "money",
            "width": 13,
        },
        # Hallintamuodon tyyppi (Subventio)
        "subvention_form_of_management": {
            "label": _("Form of management (Subvention)"),
            "source": get_subvention_form_of_management,
            "width": 20,
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
            "width": 13,
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
        # Matti-raportti
        "matti_report": {
            "label": _("Matti report"),
            "source": get_matti_report,
            "format": "boolean",
        },
        # Irtisanomisaika
        "notice_period": {
            "label": _("Notice period"),
            "source": get_notice_period,
            "width": 20,
        },
    }
    async_task_timeout = 60 * 30  # 30 minutes

    def get_data(self, input_data: LeaseStatisticReportInputData) -> QuerySet[Lease]:
        qs = Lease.objects.select_related(
            "identifier__type",
            "identifier__district",
            "identifier__municipality",
            "lessor",
            "management",
            "district",
            "supportive_housing",
            "type",
            "notice_period",
        ).prefetch_related(
            "rents",
            "rents__rent_adjustments",
            "contracts",
            "lease_areas",
            "lease_areas__addresses",
            "lease_areas__attachments",
            "decisions",
            "decisions__conditions",
            "tenants",
            "tenants__tenantcontact_set",
            "tenants__tenantcontact_set__contact",
            "basis_of_rents",
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

    def get_response(self, request: Request) -> Response:
        user_email: str = request.user.email
        async_task(
            generate_email_report,
            email=user_email,
            query_params=request.query_params,
            report_class=self.__class__,
            hook=send_email_report,
            timeout=getattr(self, "async_task_timeout", Conf.TIMEOUT),
        )

        return Response(
            {"message": _("Results will be sent by email to {}").format(user_email)}
        )

    def write_lease_basis_of_rent_column_labels(
        self, worksheet, row_number, column_number, formats
    ):
        for label in LeaseBasisOfRentRowLabels:
            worksheet.write(row_number, column_number, label, formats[FormatType.BOLD])
            column_number += 1
        return row_number + 1

    def write_lease_basis_of_rent_rows(
        self, worksheet, row_number, column_number, lease_basis_of_rent_rows, formats
    ):
        for lease_basis_of_rent_row in lease_basis_of_rent_rows:
            for attribute in lease_basis_of_rent_row:
                worksheet.write(row_number, column_number, attribute[1])
                column_number += 1
            row_number += 1
            column_number = 0
        return row_number + 1

    def data_as_excel(
        self, data: list[dict | ExcelRow], lease_basis_of_rents: list[Any]
    ):
        report = self

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        formats = {
            FormatType.BOLD: workbook.add_format({"bold": True}),
            FormatType.DATE: workbook.add_format({"num_format": "dd.mm.yyyy"}),
            FormatType.MONEY: workbook.add_format({"num_format": "#,##0.00 €"}),
            FormatType.BOLD_MONEY: workbook.add_format(
                {"bold": True, "num_format": "#,##0.00 €"}
            ),
            FormatType.PERCENTAGE: workbook.add_format({"num_format": "0.0 %"}),
            FormatType.AREA: workbook.add_format({"num_format": r"#,##0.00 \m\²"}),
        }

        row_number = 0

        # On the first row print the report name
        worksheet.write(row_number, 0, str(report.name), formats[FormatType.BOLD])

        # On the second row print the report description
        row_number += 1
        worksheet.write(row_number, 0, str(report.description))

        # On the fourth row forwards print the input fields and their values
        row_number += 2
        row_number = self.write_input_field_value_rows(
            worksheet, report.form, row_number, formats
        )

        # Set column widths
        for index, field_name in enumerate(report.output_fields.keys()):
            worksheet.set_column(
                index,
                index,
                report.get_output_field_attr(field_name, "width", default=10),
            )

        # Labels from the first non-ExcelRow row
        if report.automatic_excel_column_labels:
            row_number += 1

            lookup_row_num = 0
            while lookup_row_num < len(data) and isinstance(
                data[lookup_row_num], ExcelRow
            ):
                lookup_row_num += 1

            if len(data) > lookup_row_num:
                for index, field_name in enumerate(data[lookup_row_num].keys()):
                    field_label = report.get_output_field_attr(
                        field_name, "label", default=field_name
                    )

                    worksheet.write(
                        row_number, index, str(field_label), formats[FormatType.BOLD]
                    )

        # The data itself
        row_number += 1
        first_data_row_num = row_number
        for row in data:
            if isinstance(row, dict):
                row["lease_identifier"] = get_identifier_string_from_lease_link_data(
                    row
                )
                self.write_dict_row_to_worksheet(worksheet, formats, row_number, row)
            elif isinstance(row, ExcelRow):
                for cell in row.cells:
                    cell.set_row(row_number)
                    cell.set_first_data_row_num(first_data_row_num)
                    worksheet.write(
                        row_number,
                        cell.column,
                        cell.get_value(),
                        (
                            formats[cell.get_format_type()]
                            if cell.get_format_type() in formats
                            else None
                        ),
                    )

            row_number += 1

        # Second worksheet: Bases of rent separately

        worksheet_basis_of_rents = workbook.add_worksheet()

        row_number = 0
        column_number = 0
        worksheet_basis_of_rents.write(
            row_number,
            column_number,
            "Statistic report: Bases of rent",
            formats[FormatType.BOLD],
        )

        row_number = 1
        worksheet_basis_of_rents.write(
            row_number, column_number, "This is a hardcoded description for testing"
        )

        row_number = 3
        row_number = self.write_input_field_value_rows(
            worksheet_basis_of_rents, report.form, row_number, formats
        )

        row_number += 1

        # Column headers
        row_number = self.write_lease_basis_of_rent_column_labels(
            worksheet_basis_of_rents, row_number, column_number, formats
        )

        row_number = self.write_lease_basis_of_rent_rows(
            worksheet_basis_of_rents,
            row_number,
            column_number,
            lease_basis_of_rents,
            formats,
        )

        workbook.close()

        return output.getvalue()


def generate_email_report(
    email: str,
    query_params: dict[str, str],
    report_class: Type[LeaseStatisticReport],
) -> dict[str, Any]:
    """Generates the report based on the selected report settings."""
    del email  # Unused in this function, but needed in the hook

    report = report_class()
    input_data = report.get_input_data(query_params)
    report_data = report.get_data(input_data)

    basis_of_rents = get_basis_of_rent_rows_from_report_data(report_data)

    if isinstance(report_data, list):
        spreadsheet = report.data_as_excel(report_data, basis_of_rents)
    else:
        serialized_data = report.serialize_data(report_data)
        spreadsheet = report.data_as_excel(serialized_data, basis_of_rents)

    return {
        "report_spreadsheet": spreadsheet,
        "report_name": report.name,
        "report_filename": report.get_filename("xlsx"),
    }


def get_basis_of_rent_rows_from_report_data(
    report_data: list[dict[str, Any]]
) -> list[Any]:
    basis_of_rents = []
    for lease in report_data:
        for basis_of_rent in lease.basis_of_rents.all() or []:
            if basis_of_rent.archived_at or not basis_of_rent.locked_at:
                continue
            basis_of_rent_row = [
                ("lease_identifier", lease.get_identifier_string()),
                ("type", basis_of_rent.type.value),
                ("intended_use", basis_of_rent.intended_use.name),
                ("index", str(basis_of_rent.index)),
                ("area", basis_of_rent.area),
                ("area_unit", basis_of_rent.area_unit.value),
                ("amount_per_area", basis_of_rent.get_index_adjusted_amount_per_area()),
                ("profit_margin_percentage", basis_of_rent.profit_margin_percentage),
                ("initial_year_rent", basis_of_rent.calculate_initial_year_rent()),
                (
                    "subvention_type",
                    (
                        basis_of_rent.subvention_type.value
                        if basis_of_rent.subvention_type
                        else "-"
                    ),
                ),
                (
                    "subvented_initial_year_rent",
                    basis_of_rent.calculate_subvented_initial_year_rent(),
                ),
                (
                    "subvention_euros_per_year",
                    basis_of_rent.calculate_subvention_euros_per_year(),
                ),
                (
                    "subvention_percent",
                    basis_of_rent.calculate_subvention_percent(),
                ),
                (
                    "subvention_amount_per_area",
                    basis_of_rent.calculate_subvention_amount_per_area(),
                ),
                (
                    "subvention_base_percent",
                    basis_of_rent.subvention_base_percent,
                ),
                (
                    "subvention_graduated_percent",
                    basis_of_rent.subvention_graduated_percent,
                ),
                # TODO: implement LeaseBasisOfRent.calculate_temporary_discount_percentage
                (
                    "temporary_discount_percentage",
                    "basis_of_rent.calculate_temporary_discount_percentage()",
                ),
                # TODO: implement LeaseBasisOfRent.calculate_temporary_discount_amount_euros_per_year
                (
                    "temporary_discount_amount_euros_per_year",
                    "basis_of_rent.calculate_temporary_discount_amount_euros_per_year()",
                ),
            ]
            basis_of_rents.append(basis_of_rent_row)
    basis_of_rents.sort(key=lambda x: x[0][1])
    return basis_of_rents
