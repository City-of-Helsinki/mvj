from django import forms
from django.utils.translation import gettext_lazy as _

from leasing.models import Condition, ConditionType, ServiceUnit
from leasing.report.lease.common_getters import LeaseLinkData
from leasing.report.report_base import ReportBase


def get_lease_link_data_from_decision_condition(condition: Condition) -> LeaseLinkData:
    try:
        return {
            "id": condition.decision.lease.id,
            "identifier": condition.decision.lease.get_identifier_string(),
        }
    except AttributeError:
        return {
            "id": None,
            "identifier": None,
        }


def get_condition_type(obj):
    return obj.type.name if obj.type else ""


def get_area(obj):
    return ", ".join(
        [
            la.identifier
            for la in obj.decision.lease.lease_areas.all()
            if la.archived_at is None
        ]
    )


def get_address(obj):
    addresses = []
    for lease_area in obj.decision.lease.lease_areas.all():
        if lease_area.archived_at:
            continue

        addresses.extend([la.address for la in lease_area.addresses.all()])

    return " / ".join(addresses)


def get_tenants(obj):
    contacts = []
    for tenant in obj.decision.lease.tenants.all():
        for contact in tenant.contacts.filter(
            tenantcontact__end_date__isnull=True,
            tenantcontact__tenant_id=tenant.id,
            tenantcontact__type="tenant",
        ):
            if contact.name:
                contacts.append(contact.name)
            elif contact.first_name and contact.last_name:
                contacts.append(contact.first_name + " " + contact.last_name)
            else:
                contacts.append("Null")

    return " / ".join(contacts)


class DecisionConditionsReport(ReportBase):
    name = _("Decision conditions")
    description = _(
        "Show decision conditions that have their supervision date between the given dates. "
        "Excluding conditions that have a supervised date."
    )
    slug = "decision_conditions"
    input_fields = {
        "service_unit": forms.ModelMultipleChoiceField(
            label=_("Service unit"),
            queryset=ServiceUnit.objects.all(),
            required=False,
        ),
        "start_date": forms.DateField(label=_("Start date"), required=False),
        "end_date": forms.DateField(label=_("End date"), required=False),
        "condition_type": forms.ModelChoiceField(
            label=_("Type"),
            queryset=ConditionType.objects.all(),
            empty_label=None,
            required=False,
        ),
        "supervision_exists": forms.ChoiceField(
            choices=[("True", _("Yes")), ("False", _("No"))],
            label=_("Supervision date exists"),
            required=False,
        ),
    }
    output_fields = {
        "lease_identifier": {
            "source": get_lease_link_data_from_decision_condition,
            "label": _("Lease id"),
        },
        "area": {"source": get_area, "label": _("Lease area"), "width": 30},
        "address": {"source": get_address, "label": _("Address"), "width": 50},
        "type": {"source": get_condition_type, "label": _("Type"), "width": 25},
        "supervision_date": {
            "label": _("Supervision date"),
            "format": "date",
            "width": 15,
        },
        # Always empty due to filtering
        # 'supervised_date': {
        #     'label': _('Supervised date'),
        #     'format': 'date',
        # },
        "description": {"label": _("Description"), "width": 100},
        "tenants": {"source": get_tenants, "label": _("Tenants"), "width": 50},
    }

    def get_data(self, input_data):
        qs = (
            Condition.objects.filter(supervised_date__isnull=True)
            .exclude(deleted__isnull=False)
            .exclude(decision__deleted__isnull=False)
            .exclude(decision__lease__deleted__isnull=False)
            .select_related(
                "type",
                "decision",
                "decision__lease",
                "decision__lease__identifier",
                "decision__lease__identifier__type",
                "decision__lease__identifier__district",
                "decision__lease__identifier__municipality",
            )
            .prefetch_related(
                "decision__lease__lease_areas",
                "decision__lease__lease_areas__addresses",
                "decision__lease__tenants",
                "decision__lease__tenants__contacts",
            )
            .order_by(
                "supervision_date",
                "decision__lease__identifier__type__identifier",
                "decision__lease__identifier__municipality__identifier",
                "decision__lease__identifier__district__identifier",
                "decision__lease__identifier__sequence",
            )
        )

        if input_data["service_unit"]:
            qs = qs.filter(decision__lease__service_unit__in=input_data["service_unit"])

        if input_data["supervision_exists"]:
            if input_data["supervision_exists"] == "True":
                qs = qs.filter(supervision_date__isnull=False)
            else:
                qs = qs.filter(supervision_date__isnull=True)

        if input_data["start_date"]:
            qs = qs.filter(supervision_date__gte=input_data["start_date"])

        if input_data["end_date"]:
            qs = qs.filter(supervision_date__lte=input_data["end_date"])

        if input_data["condition_type"]:
            qs = qs.filter(type=input_data["condition_type"])

        qs = qs.order_by("decision__lease__identifier__type__identifier")

        return qs
