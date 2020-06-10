from django import forms
from django.db.models import Count, Q
from django.utils.translation import ugettext_lazy as _

from leasing.enums import LeaseListType, RentType, TenantContactType
from leasing.models import Lease
from leasing.report.excel import ExcelCell, ExcelRow, FormatType
from leasing.report.report_base import AsyncReportBase


class LeaseListsReport(AsyncReportBase):
    name = _("Lease lists")
    description = _("Lists of leases that satisfy different criteria")
    slug = "lease_lists"
    input_fields = {
        "start_date": forms.DateField(label=_("Start date"), required=True),
        "end_date": forms.DateField(label=_("End date"), required=True),
    }
    output_fields = {
        "lease_id": {"label": _("Lease id")},
        "start_date": {"label": _("Start date"), "format": "date"},
        "end_date": {"label": _("End date"), "format": "date"},
    }
    automatic_excel_column_labels = False
    async_task_timeout = 60 * 60  # 60 minutes

    def get_data(self, input_data):  # NOQA C901
        qs = (
            (
                Lease.objects.filter(
                    (
                        Q(start_date__isnull=True)
                        | Q(start_date__lte=input_data["end_date"])
                    )
                    & (
                        Q(end_date__isnull=True)
                        | Q(end_date__gte=input_data["start_date"])
                    )
                )
            )
            .prefetch_related(
                "lease_areas",
                "rents",
                "tenants",
                "tenants__tenantcontact_set",
                "tenants__tenantcontact_set__contact",
                "tenants__rent_shares",
            )
            .annotate(rent_count=Count("rents"))
            .annotate(lease_area_count=Count("lease_areas"))
        )

        aggregated_data = {}
        for lease_list_type in LeaseListType:
            aggregated_data[lease_list_type.value] = {
                "label": lease_list_type.label,
                "leases": [],
            }

        for lease in qs:

            # 1.1 Vuokraukset, joissa ei ole laskutus käynnissä
            if not lease.is_invoicing_enabled:
                aggregated_data[LeaseListType.INVOICING_NOT_ENABLED.value][
                    "leases"
                ].append(lease)

            # 1.2 Vuokraukset, joissa ei ole vuokratiedot kunnossa
            if not lease.is_rent_info_complete:
                aggregated_data[LeaseListType.RENT_INFO_NOT_COMPLETE.value][
                    "leases"
                ].append(lease)

            # 1.3 Vuokraukset, joissa ei ole vuokratietoja
            if lease.rent_count == 0:
                aggregated_data[LeaseListType.NO_RENTS.value]["leases"].append(lease)

            # 1.4 Vuokraukset, joissa ei ole eräpäivää
            due_dates = False
            for rent in lease.rents.all():
                if not rent.type:
                    continue
                if rent.due_dates.count() > 0:
                    due_dates = True
                    break
            if not due_dates:
                aggregated_data[LeaseListType.NO_DUE_DATE.value]["leases"].append(lease)

            # 1.5 Vuokraukset, joilla on kertakaikkinen vuokra mutta ei ole laskuja.
            for rent in lease.rents.all():
                if rent.type == RentType.ONE_TIME and lease.invoices.count() == 0:
                    aggregated_data[LeaseListType.ONE_TIME_RENTS_WITH_NO_INVOICE.value][
                        "leases"
                    ].append(lease)
                    break

            # 1.6 Vuokraukset, joissa on virheellinen hallintaosuus
            management_sum = 0
            for tenant in lease.tenants.all():
                management_sum = (
                    management_sum + tenant.share_numerator / tenant.share_denominator
                )
            if management_sum != 1:
                aggregated_data[LeaseListType.INCORRECT_MANAGEMENT_SHARES.value][
                    "leases"
                ].append(lease)

            # 1.7 Vuokraukset, joissa on virheellinen laskutusosuus
            rent_share_sum = 0
            for tenant in lease.tenants.all():
                for rent_share in tenant.rent_shares.all():
                    rent_share_sum = (
                        rent_share_sum
                        + rent_share.share_numerator / rent_share.share_denominator
                    )
            if rent_share_sum != 1:
                aggregated_data[LeaseListType.INCORRECT_RENT_SHARES.value][
                    "leases"
                ].append(lease)

            # 1.8 Vuokraukset, joissa ei ole voimassaolevaa vuokraajaa
            valid_tenant = False
            for tenant in lease.tenants.all():
                for tc in tenant.tenantcontact_set.all():
                    if tc.type != TenantContactType.TENANT:
                        continue
                    if (
                        tc.end_date is None or tc.end_date >= input_data["end_date"]
                    ) and (
                        tc.start_date is None or tc.start_date <= input_data["end_date"]
                    ):
                        valid_tenant = True
            if not valid_tenant:
                aggregated_data[LeaseListType.NO_TENANT_CONTACT.value]["leases"].append(
                    lease
                )

            # 1.9 Vuokraukset, joissa ei ole vuokrakohdetta
            if lease.lease_area_count == 0:
                aggregated_data[LeaseListType.NO_LEASE_AREA.value]["leases"].append(
                    lease
                )

        result = []
        for report in aggregated_data:

            # Intermediate heading: name of list
            result.append(
                ExcelRow(
                    [
                        ExcelCell(
                            column=0,
                            value=str(aggregated_data.get(report)["label"]),
                            format_type=FormatType.BOLD,
                        )
                    ]
                )
            )

            # Field labels as reminders under each list name heading
            result.append(
                ExcelRow(
                    [
                        ExcelCell(
                            column=i,
                            value=str(self.output_fields[key]["label"]),
                            format_type=FormatType.BOLD,
                        )
                        for i, key in enumerate(self.output_fields)
                    ]
                )
            )

            for lease in aggregated_data.get(report)["leases"]:
                result.append(
                    {
                        "lease_id": lease.get_identifier_string(),
                        "start_date": lease.start_date,
                        "end_date": lease.end_date if lease.end_date else "-",
                    }
                )

            result.append(ExcelRow())
            result.append(ExcelRow())

        return result
