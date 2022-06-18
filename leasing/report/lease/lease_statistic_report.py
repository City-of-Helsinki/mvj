import datetime
from collections import defaultdict
from decimal import Decimal
from functools import lru_cache

from django import forms
from django.db.models import Q
from django.utils import formats
from django.utils.translation import ugettext_lazy as _
from enumfields.drf import EnumField

from leasing.enums import LeaseAreaAttachmentType, LeaseState
from leasing.models import Lease
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

# TODO: Can we get rid of static ids
RESIDENTIAL_INTENDED_USE_IDS = [
    1,
    12,
    13,
]  # 1 = Asunto, 12 = Asunto, lisärakent., 13 = Asunto 2


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
        if basis_of_rent.intended_use_id not in RESIDENTIAL_INTENDED_USE_IDS:
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
        if basis_of_rent.intended_use_id in RESIDENTIAL_INTENDED_USE_IDS:
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
def _get_rent_amount_for_year(obj, year):
    return obj.calculate_rent_amount_for_year(year)


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


class LeaseStatisticReport(AsyncReportBase):
    name = _("Lease statistics report")
    description = _(
        "Shows information about all leases or if start date is provided the leases that have started on or after it"
    )
    slug = "lease_statistic"
    input_fields = {
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
        "tenants": {"label": _("Tenants"), "source": get_tenants, "width": 40},
        # Start date
        "start_date": {"label": _("Start date"), "format": "date"},
        # End date
        "end_date": {"label": _("End date"), "format": "date"},
        # Kokonaispinta-ala
        "total_area": {"label": _("Total area"), "source": get_total_area},
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
        # Hallintamuoto
        "form_of_management": {
            "label": _("Form of management"),
            "source": get_form_of_management,
            "width": 13,
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

    def get_data(self, input_data):
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
