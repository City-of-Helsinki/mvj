import datetime
from decimal import Decimal
from itertools import groupby
from operator import itemgetter

from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework.request import Request
from rest_framework.response import Response

from leasing.enums import TenantContactType
from leasing.models import Invoice, ServiceUnit
from leasing.report.excel import (
    ExcelCell,
    ExcelRow,
    FormatType,
    PreviousRowsSumCell,
    SumCell,
)
from leasing.report.report_base import ReportBase


def get_lease_ids(obj):
    return {
        "id": obj.lease.id,
        "identifier": obj.lease.get_identifier_string(),
    }


def get_recipient_address(obj):
    return ", ".join(
        filter(
            None, [obj.recipient.address, obj.recipient.postal_code, obj.recipient.city]
        )
    )


def get_contract_number(obj):
    contract_numbers = []
    for contract in obj.contracts.all():
        if not contract.contract_number:
            continue

        contract_numbers.append(contract.contract_number)

    return " / ".join(contract_numbers)


def get_lease_area_identifier(obj):
    lease_area_identifiers = []

    for lease_area in obj.lease_areas.all():
        if lease_area.archived_at:
            continue

        lease_area_identifiers.extend([lease_area.identifier])

    return " / ".join(lease_area_identifiers)


def get_address(obj):
    addresses = []

    for lease_area in obj.lease_areas.all():
        if lease_area.archived_at:
            continue

        for area_address in lease_area.addresses.all():
            if not area_address.is_primary:
                continue

            addresses.append(area_address.address)

    return " / ".join(addresses)


def get_tenants(obj):
    today = datetime.date.today()

    contacts = set()

    for tenant in obj.tenants.all():
        for tc in tenant.tenantcontact_set.all():
            if tc.type != TenantContactType.TENANT:
                continue

            if (tc.end_date is None or tc.end_date >= today) and (
                tc.start_date is None or tc.start_date <= today
            ):
                contacts.add(tc.contact)

    return ", ".join([c.get_name() for c in contacts])


def get_total_area(obj):
    total_area = 0
    for lease_area in obj.lease_areas.all():
        if lease_area.archived_at:
            continue

        total_area += lease_area.area

    return total_area


class ExtraCityRentReport(ReportBase):
    name = _("Extra city rent")
    description = _("The invoiced rent of the leases that are not in the main city")
    slug = "extra_city_rent"
    input_fields = {
        "service_unit": forms.ModelMultipleChoiceField(
            label=_("Service unit"),
            queryset=ServiceUnit.objects.all(),
            required=False,
        ),
        "start_date": forms.DateField(label=_("Start date"), required=True),
        "end_date": forms.DateField(label=_("End date"), required=True),
    }
    output_fields = {
        "lease_id": {"label": _("Lease id")},
        "tenant_name": {"label": _("Tenant name"), "width": 50},
        "area_identifier": {"label": _("Area identifier"), "width": 50},
        "area": {"label": _("Area amount"), "format": "area"},
        "area_address": {"label": _("Address"), "width": 50},
        "rent": {"label": _("Rent"), "format": "money", "width": 13},
        "contract_number": {"label": _("Contract number"), "is_numeric": True},
        "lease_area_identifier": {"label": _("Lease area identifier"), "width": 20},
        "address": {"label": _("Address"), "width": 20},
        "tenants": {"label": _("Tenants"), "width": 40},
        "start_date": {"label": _("Start date"), "format": "date"},
        "end_date": {"label": _("End date"), "format": "date"},
        "intended_use": {"label": _("Intended use")},
        "total_area": {"label": _("Total area"), "format": "area"},
    }
    automatic_excel_column_labels = False

    def get_data(self, input_data):
        qs = (
            Invoice.objects.filter(
                (
                    Q(rows__billing_period_start_date__gte=input_data["start_date"])
                    & Q(rows__billing_period_start_date__lte=input_data["end_date"])
                )
                | (
                    Q(rows__billing_period_end_date__gte=input_data["start_date"])
                    & Q(rows__billing_period_end_date__lte=input_data["end_date"])
                )
            )
            .exclude(lease__municipality=1)  # Helsinki
            .select_related(
                "lease",
                "lease__identifier",
                "lease__identifier__type",
                "lease__identifier__district",
                "lease__identifier__municipality",
            )
            .prefetch_related(
                "lease__tenants",
                "lease__tenants__tenantcontact_set",
                "lease__tenants__tenantcontact_set__contact",
                "lease__lease_areas",
                "lease__lease_areas__addresses",
            )
            .order_by(
                "lease__identifier__municipality__identifier",
                "lease__identifier__type__identifier",
                "lease__identifier__district__identifier",
                "lease__identifier__sequence",
            )
        )

        if input_data["service_unit"]:
            qs = qs.filter(service_unit__in=input_data["service_unit"])

        aggregated_data = []

        for lease, invoices in groupby(qs, lambda x: x.lease):
            total_rent = Decimal(0)
            contacts = set()
            for invoice in invoices:
                total_rent += invoice.total_amount

            # Do this in code so that the prefetch is used
            for tenant in lease.tenants.all():
                for tc in tenant.tenantcontact_set.all():
                    if tc.type != TenantContactType.TENANT:
                        continue

                    if (
                        tc.end_date is None or tc.end_date >= input_data["start_date"]
                    ) and (
                        tc.start_date is None or tc.start_date <= input_data["end_date"]
                    ):
                        contacts.add(tc.contact)

            addresses = []
            for lease_area in lease.lease_areas.all():
                if lease_area.archived_at:
                    continue

                addresses.extend([la.address for la in lease_area.addresses.all()])

            aggregated_data.append(
                {
                    "municipality_name": lease.identifier.municipality.name,
                    "lease_id": get_lease_ids(lease),
                    "tenant_name": ", ".join([c.get_name() for c in contacts]),
                    "area_identifier": ", ".join(
                        [
                            la.identifier
                            for la in lease.lease_areas.all()
                            if la.archived_at is None
                        ]
                    ),
                    "area": sum(
                        [
                            la.area
                            for la in lease.lease_areas.all()
                            if la.archived_at is None
                        ]
                    ),
                    "area_address": " / ".join(addresses),
                    "rent": total_rent,
                    "contract_number": get_contract_number(lease),
                    "lease_area_identifier": get_lease_area_identifier(lease),
                    "address": get_address(lease),
                    "tenants": get_tenants(lease),
                    "start_date": lease.start_date,
                    "end_date": lease.end_date,
                    "intended_use": (
                        lease.intended_use.name if lease.intended_use else None
                    ),
                    "total_area": get_total_area(lease),
                }
            )

        return aggregated_data

    def get_response(self, request: Request) -> Response:
        input_data = self.get_input_data(request.query_params)
        report_data = self.get_data(input_data)

        if request.accepted_renderer.format != "xlsx":
            serialized_report_data = self.serialize_data(report_data)

            return Response(serialized_report_data)

        grouped_data = groupby(report_data, itemgetter("municipality_name"))

        result = []
        totals_row_nums = []
        data_row_num = 0

        for municipality_name, data in grouped_data:
            result.append(ExcelRow())
            data_row_num += 1
            result.append(ExcelRow())
            data_row_num += 1

            result.append(
                ExcelRow(
                    [
                        ExcelCell(
                            column=0,
                            value=municipality_name,
                            format_type=FormatType.BOLD,
                        )
                    ]
                )
            )
            data_row_num += 1

            result.append(ExcelRow())
            data_row_num += 1

            column_names_row = ExcelRow()
            for index, field_name in enumerate(self.output_fields.keys()):
                field_label = self.get_output_field_attr(
                    field_name, "label", default=field_name
                )
                column_names_row.cells.append(
                    ExcelCell(
                        column=index,
                        value=str(field_label),
                        format_type=FormatType.BOLD,
                    )
                )
            result.append(column_names_row)
            data_row_num += 1

            row_count = 0
            for datum in data:
                datum.pop("municipality_name")
                result.append(datum)
                row_count += 1
                data_row_num += 1

            total_row = ExcelRow(
                [
                    ExcelCell(
                        column=0,
                        value="{} {}".format(municipality_name, _("Total")),
                        format_type=FormatType.BOLD,
                    ),
                    PreviousRowsSumCell(
                        column=3, count=row_count, format_type=FormatType.AREA
                    ),
                    PreviousRowsSumCell(
                        column=5, count=row_count, format_type=FormatType.BOLD_MONEY
                    ),
                ]
            )
            result.append(total_row)
            totals_row_nums.append(data_row_num)

            data_row_num += 1

        result.append(ExcelRow())

        totals_row = ExcelRow()
        totals_row.cells.append(
            ExcelCell(
                column=0, value=str(_("Grand total")), format_type=FormatType.BOLD
            )
        )

        total_area_sum_cell = SumCell(column=3, format_type=FormatType.AREA)
        total_rent_sum_cell = SumCell(column=5, format_type=FormatType.BOLD_MONEY)
        for totals_row_num in totals_row_nums:
            total_area_sum_cell.add_target_range((totals_row_num, 3, totals_row_num, 3))
            total_rent_sum_cell.add_target_range((totals_row_num, 5, totals_row_num, 5))

        totals_row.cells.append(total_area_sum_cell)
        totals_row.cells.append(total_rent_sum_cell)
        result.append(totals_row)

        return Response(result)
