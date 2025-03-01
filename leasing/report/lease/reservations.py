import datetime
import itertools

from django import forms
from django.db import connection
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from leasing.enums import ContactType, LeaseState, TenantContactType
from leasing.models import Lease, ServiceUnit
from leasing.report.lease.common_getters import get_lease_link_data
from leasing.report.report_base import ReportBase


def get_area(lease):
    return ", ".join(
        [la.identifier for la in lease.lease_areas.all() if la.archived_at is None]
    )


def get_address(lease):
    addresses = set()
    for lease_area in lease.lease_areas.all():
        if lease_area.archived_at:
            continue

        addresses.update([la.address for la in lease_area.addresses.all()])

    return " / ".join(addresses)


def get_tenants(lease):
    today = datetime.date.today()

    contacts = set()

    for tenant in lease.tenants.all():
        for tc in tenant.tenantcontact_set.all():
            if tc.type != TenantContactType.TENANT:
                continue

            if (tc.end_date is None or tc.end_date >= today) and (
                tc.start_date is None or tc.start_date <= today
            ):
                contacts.add(tc.contact)

    contact_strings = []
    for contact in contacts:
        contact_string = contact.get_name()

        if contact.type == ContactType.BUSINESS and contact.business_id:
            contact_string += f" ({contact.business_id})"

        contact_strings.append(contact_string)

    return ", ".join(contact_strings)


def get_reservation_procedure(lease):
    return lease.reservation_procedure.name if lease.reservation_procedure else None


def get_plan_unit_intended_uses(lease):
    plan_units_intended_uses = []
    for lease_area in lease.lease_areas.all():
        if lease_area.archived_at:
            continue
        for plan_unit in lease_area.plan_units.all():
            if plan_unit.plan_unit_intended_use:
                plan_units_intended_uses.append(plan_unit.plan_unit_intended_use.name)

    return ", ".join(plan_units_intended_uses)


def get_plan_unit_detailed_plan_identifier(lease):
    plan_units_detailed_plan_identifiers = []
    for lease_area in lease.lease_areas.all():
        if lease_area.archived_at:
            continue
        for plan_unit in lease_area.plan_units.all():
            if plan_unit.detailed_plan_identifier:
                plan_units_detailed_plan_identifiers.append(
                    plan_unit.detailed_plan_identifier
                )

    return ", ".join(plan_units_detailed_plan_identifiers)


def get_plan_unit_usage_distribution_main_build_permission(lease):
    """
    build permission of usage distribution with highest build permission
    """
    main_build_permission = 0
    for lease_area in lease.lease_areas.all():
        if lease_area.archived_at:
            continue
        for plan_unit in lease_area.plan_units.all():
            for usage_distribution in plan_unit.usage_distributions.all():
                if (
                    usage_distribution.build_permission.isdigit()
                    and int(usage_distribution.build_permission) > main_build_permission
                ):
                    main_build_permission = int(usage_distribution.build_permission)

    if main_build_permission != 0:
        return str(main_build_permission)
    else:
        return ""


def get_plan_unit_usage_distribution_other_build_permission(lease):
    """
    aggregate build permission of all usage distributions except usage distribution with highest build permission
    """
    other_build_permission = 0
    highest_build_permission = 0
    for lease_area in lease.lease_areas.all():
        if lease_area.archived_at:
            continue
        for plan_unit in lease_area.plan_units.all():
            for usage_distribution in plan_unit.usage_distributions.all():
                if usage_distribution.build_permission.isdigit():
                    current_build_permission = int(usage_distribution.build_permission)
                    other_build_permission += current_build_permission
                    if current_build_permission > highest_build_permission:
                        highest_build_permission = current_build_permission
    if other_build_permission != 0:
        return str(other_build_permission - highest_build_permission)
    else:
        return ""


def get_financing_name(lease):
    if lease.financing:
        return lease.financing.name
    else:
        return ""


def get_management_name(lease):
    if lease.management:
        return lease.management.name
    else:
        return ""


class ReservationsReport(ReportBase):
    name = _("Reservations")
    description = _("Show reservations")
    slug = "reservations"
    input_fields = {
        "service_unit": forms.ModelMultipleChoiceField(
            label=_("Service unit"),
            queryset=ServiceUnit.objects.all(),
            required=False,
        ),
        "start_date_start": forms.DateField(
            label=_("Start date start"), required=False
        ),
        "start_date_end": forms.DateField(label=_("Start date end"), required=False),
        "end_date_start": forms.DateField(label=_("End date start"), required=False),
        "end_date_end": forms.DateField(label=_("End date end"), required=False),
        "exclude_leases": forms.BooleanField(
            label=_("Exclude ones that are related to a lease"),
            initial=False,
            required=False,
        ),
        "exclude_sold": forms.NullBooleanField(
            label=_("Exclude sold"), initial=False, required=False
        ),
    }
    output_fields = {
        "lease_identifier": {
            "source": get_lease_link_data,
            "label": _("Reservation id"),
        },
        "area": {"source": get_area, "label": _("Lease area"), "width": 30},
        "address": {"source": get_address, "label": _("Address"), "width": 50},
        "reservee_name": {
            "source": get_tenants,
            "label": _("Reservee name"),
            "width": 50,
        },
        "reservation_procedure": {
            "source": get_reservation_procedure,
            "label": _("Reservation procedure"),
            "width": 50,
        },
        "start_date": {"label": _("Start date"), "format": "date"},
        "end_date": {"label": _("End date"), "format": "date"},
        "plan_unit_intended_uses": {
            "source": get_plan_unit_intended_uses,
            "label": _("Plan unit intended use"),
            "width": 50,
        },
        "plan_unit_detailed_plan_identifier": {
            "source": get_plan_unit_detailed_plan_identifier,
            "label": _("Plan number"),
            "width": 50,
        },
        "plan_unit_usage_distribution_main_build_permission": {
            "source": get_plan_unit_usage_distribution_main_build_permission,
            "label": _("Main permitted build area (floor-m²)"),
            "width": 50,
        },
        "plan_unit_usage_distribution_other_build_permission": {
            "source": get_plan_unit_usage_distribution_other_build_permission,
            "label": _("Other permitted build area (floor-m²)"),
            "width": 50,
        },
        "financing": {
            "source": get_financing_name,
            "label": _("Financing method"),
            "width": 50,
        },
        "management": {
            "source": get_management_name,
            "label": _("Management method"),
            "width": 50,
        },
    }

    def get_data(self, input_data):  # NOQA C901
        lease_ids = []

        if input_data["exclude_leases"] is True:
            service_unit_where = ""
            if input_data["service_unit"]:
                service_unit_where = " AND l.service_unit_id IN ({})".format(
                    ", ".join([str(su.id) for su in input_data["service_unit"]])
                )

            dates_where_parts = []
            # The date where clause is generated here by hand including user input,
            # but it shouldn't be a problem because the input is validated
            # to be a valid date.
            if input_data["start_date_start"]:
                dates_where_parts.append(
                    "(l.start_date IS NULL OR l.start_date >= '{}'::date)".format(
                        input_data["start_date_start"]
                    )
                )

            if input_data["start_date_end"]:
                dates_where_parts.append(
                    "(l.start_date IS NULL OR l.start_date <= '{}'::date)".format(
                        input_data["start_date_end"]
                    )
                )

            if input_data["end_date_start"]:
                dates_where_parts.append(
                    "(l.end_date IS NULL OR l.end_date >= '{}'::date)".format(
                        input_data["end_date_start"]
                    )
                )

            if input_data["end_date_end"]:
                dates_where_parts.append(
                    "(l.end_date IS NULL OR l.end_date <= '{}'::date)".format(
                        input_data["end_date_end"]
                    )
                )

            dates_where = ""
            if dates_where_parts:
                dates_where = " AND " + " AND ".join(dates_where_parts)

            with connection.cursor() as cursor:
                # This query creates a Common Table Expression (CTE) which
                # goes through the leasing_relatedlease relations from the
                # "from lease" to the last related "to lease" (l2).
                #
                # That is because reservations can be chained, but we need
                # to find if there eventually is a lease in the end of the chain.
                cursor.execute(
                    """
                    WITH RECURSIVE relations(from_lease, last_to_lease) AS (
                       SELECT
                          rl.from_lease_id,
                          rl.to_lease_id
                       FROM
                          leasing_relatedlease rl
                       LEFT JOIN
                          leasing_relatedlease p ON rl.to_lease_id = p.from_lease_id
                       WHERE
                          p.from_lease_id IS NULL
                       UNION
                       SELECT
                          from_lease_id,
                          last_to_lease
                       FROM
                          relations
                       INNER JOIN
                          leasing_relatedlease on relations.from_lease = leasing_relatedlease.to_lease_id
                    )
                    SELECT l.id
                    FROM leasing_lease l
                    LEFT JOIN relations ON relations.from_lease = l.id
                    LEFT JOIN leasing_lease l2 ON l2.id = relations.last_to_lease
                    WHERE l.state = 'reservation'
                    {service_unit_where}
                    {conveyance_where}
                    {dates_where}
                    AND (l2.id IS NULL OR l2.state = 'reservation');
                """.format(
                        service_unit_where=service_unit_where,
                        conveyance_where=(
                            " AND l.conveyance_number IS NULL"
                            if input_data["exclude_sold"]
                            else ""
                        ),
                        dates_where=dates_where,
                    )
                )

                # Flatten list of tuples to a list
                lease_ids.extend(itertools.chain.from_iterable(cursor))
        else:
            qs = Lease.objects.filter(state=LeaseState.RESERVATION)

            if input_data["service_unit"]:
                qs = qs.filter(service_unit__in=input_data["service_unit"])

            if input_data["start_date_start"]:
                qs = qs.filter(
                    Q(start_date__isnull=True)
                    | Q(start_date__gte=input_data["start_date_start"])
                )

            if input_data["start_date_end"]:
                qs = qs.filter(
                    Q(start_date__isnull=True)
                    | Q(start_date__lte=input_data["start_date_end"])
                )

            if input_data["end_date_start"]:
                qs = qs.filter(
                    Q(end_date__isnull=True)
                    | Q(end_date__gte=input_data["end_date_start"])
                )

            if input_data["end_date_end"]:
                qs = qs.filter(
                    Q(end_date__isnull=True)
                    | Q(end_date__lte=input_data["end_date_end"])
                )

            if input_data["exclude_sold"] is True:
                qs = qs.filter(conveyance_number__isnull=True)

            lease_ids = qs.values_list("id", flat=True)

        # Gather data about the leases
        leases = (
            Lease.objects.filter(id__in=lease_ids)
            .select_related(
                "identifier",
                "identifier__type",
                "identifier__district",
                "identifier__municipality",
                "reservation_procedure",
                "financing",
                "management",
            )
            .prefetch_related(
                "tenants",
                "tenants__tenantcontact_set",
                "tenants__tenantcontact_set__contact",
                "lease_areas",
                "lease_areas__addresses",
                "lease_areas__plan_units",
                "lease_areas__plan_units__plan_unit_intended_use",
                "lease_areas__plan_units__usage_distributions",
            )
            .order_by("start_date", "end_date")
        )

        return leases
