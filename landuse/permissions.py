from rest_framework import permissions

from landuse.models.agreement import (
    AgreementAddress,
    AgreementPreparer,
    AuthorizedSignatory,
    DetailedPlan,
    District,
    LandUseAgreement,
)
from landuse.models.compensation import LandPolicyProgram
from landuse.models.invoice import Invoice, ShadowSalesLedgerEntry
from landuse.models.payment_schedule import PaymentSchedule
from landuse.models.site import (
    SiteIntendedUse,
    SiteTenureType,
)
from utils.group_permissions import UG, GroupModelPermissions


def tab_permission(tab):
    class HasTabPermission(permissions.BasePermission):
        def has_permission(self, request, view):
            if request.method == "OPTIONS":
                return bool(request.user and request.user.is_authenticated)
            verb = {
                "GET": "view",
                "HEAD": "view",
                "PUT": "change",
                "PATCH": "change",
                "POST": "change",
                "DELETE": "change",
            }.get(request.method)
            return bool(
                verb
                and request.user
                and request.user.is_authenticated
                and request.user.has_perm(f"landuse.{verb}_tab_{tab}")
            )

    return HasTabPermission


LANDUSE_GROUP_MODEL_PERMISSIONS: GroupModelPermissions = {
    # LandUseAgreement holds tab specific permissions.
    LandUseAgreement: {
        "model": {
            UG.SELAILIJA: (
                "view",
                "view_tab_parties",
                "view_tab_sites",
                "view_tab_compensation",
                "view_tab_decisions",
                "view_tab_contracts",
            ),
            UG.VALMISTELIJA: (
                "view",
                "add",
                "change",
                "view_tab_parties",
                "change_tab_parties",
                "view_tab_sites",
                "change_tab_sites",
                "view_tab_compensation",
                "change_tab_compensation",
                "view_tab_decisions",
                "change_tab_decisions",
                "view_tab_contracts",
                "change_tab_contracts",
                "view_tab_payment_schedules",
                "change_tab_payment_schedules",
                "view_tab_invoices",
            ),
            UG.SOPIMUSVALMISTELIJA: (
                "view",
                "change",
                "view_tab_parties",
                "change_tab_parties",
                "view_tab_sites",
                "view_tab_compensation",
                "view_tab_decisions",
                "change_tab_decisions",
                "view_tab_contracts",
                "change_tab_contracts",
                "view_tab_payment_schedules",
                "view_tab_invoices",
            ),
            UG.LASKUTTAJA: (
                "view",
                "view_tab_parties",
                "change_tab_parties",
                "view_tab_sites",
                "view_tab_compensation",
                "view_tab_decisions",
                "view_tab_contracts",
                "view_tab_payment_schedules",
                "view_tab_invoices",
                "change_tab_invoices",
            ),
            UG.PAAKAYTTAJA: (
                "view",
                "add",
                "change",
                "delete",
                "view_tab_parties",
                "change_tab_parties",
                "view_tab_sites",
                "change_tab_sites",
                "view_tab_compensation",
                "change_tab_compensation",
                "view_tab_decisions",
                "change_tab_decisions",
                "view_tab_contracts",
                "change_tab_contracts",
                "view_tab_payment_schedules",
                "change_tab_payment_schedules",
                "view_tab_invoices",
                "change_tab_invoices",
            ),
        },
        "fields": {},
    },
    # Other than LandUseAgreement, permissions are model specific only,
    # unless there are custom operations defined.
    AgreementAddress: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change"),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    AgreementPreparer: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view",),
        },
        "fields": {},
    },
    AuthorizedSignatory: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    DetailedPlan: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view",),
        },
        "fields": {},
    },
    District: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Invoice: {
        "model": {
            UG.LASKUTTAJA: ("send_invoice_to_sap",),
            UG.PAAKAYTTAJA: ("send_invoice_to_sap",),
        },
        "fields": {},
    },
    LandPolicyProgram: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PaymentSchedule: {
        "model": {
            UG.LASKUTTAJA: ("approve_paymentschedule",),
            UG.PAAKAYTTAJA: ("approve_paymentschedule",),
        },
        "fields": {},
    },
    ShadowSalesLedgerEntry: {
        "model": {
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view",),
        },
        "fields": {},
    },
    SiteIntendedUse: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    SiteTenureType: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
}


class LanduseDjangoModelPermissions(permissions.DjangoModelPermissions):
    """
    Customized Django REST Framework DjangoModelPermissions
    class that includes checking for the "view" permissions too.

    Duplicated from leasing.permissions.MvjDjangoModelPermissions in order
    to decouple the landuse app from any implicit leasing configurations, and
    allow possible customizations.
    """

    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": [],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }
