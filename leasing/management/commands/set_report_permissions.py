from enum import IntEnum

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from leasing.report.viewset import ENABLED_REPORTS


class UserGroup(IntEnum):
    SELAILIJA = 1
    VALMISTELIJA = 2
    SOPIMUSVALMISTELIJA = 3
    SYOTTAJA = 4
    PERINTALAKIMIES = 5
    LASKUTTAJA = 6
    PAAKAYTTAJA = 7


UG = UserGroup


DEFAULT_REPORT_PERMS = {
    "collaterals": [UG.PERINTALAKIMIES, UG.LASKUTTAJA, UG.PAAKAYTTAJA],
    "contact_rents": [
        UG.VALMISTELIJA,
        UG.SOPIMUSVALMISTELIJA,
        UG.SYOTTAJA,
        UG.PERINTALAKIMIES,
        UG.LASKUTTAJA,
        UG.PAAKAYTTAJA,
    ],
    "decision_conditions": [
        UG.VALMISTELIJA,
        UG.SOPIMUSVALMISTELIJA,
        UG.SYOTTAJA,
        UG.PERINTALAKIMIES,
        UG.LASKUTTAJA,
        UG.PAAKAYTTAJA,
    ],
    "extra_city_rent": [
        UG.VALMISTELIJA,
        UG.SOPIMUSVALMISTELIJA,
        UG.SYOTTAJA,
        UG.PERINTALAKIMIES,
        UG.LASKUTTAJA,
        UG.PAAKAYTTAJA,
    ],
    "index_types": [
        UG.VALMISTELIJA,
        UG.SOPIMUSVALMISTELIJA,
        UG.SYOTTAJA,
        UG.PERINTALAKIMIES,
        UG.LASKUTTAJA,
        UG.PAAKAYTTAJA,
    ],
    "invoice_payments": [UG.PERINTALAKIMIES, UG.LASKUTTAJA, UG.PAAKAYTTAJA],
    "invoices_in_period": [UG.PERINTALAKIMIES, UG.LASKUTTAJA, UG.PAAKAYTTAJA],
    "invoicing_review": [UG.PERINTALAKIMIES, UG.LASKUTTAJA, UG.PAAKAYTTAJA],
    "laske_invoice_count": [UG.PERINTALAKIMIES, UG.LASKUTTAJA, UG.PAAKAYTTAJA],
    "lease_count": [
        UG.VALMISTELIJA,
        UG.SOPIMUSVALMISTELIJA,
        UG.SYOTTAJA,
        UG.PERINTALAKIMIES,
        UG.LASKUTTAJA,
        UG.PAAKAYTTAJA,
    ],
    "lease_invoicing_disabled": [UG.PERINTALAKIMIES, UG.LASKUTTAJA, UG.PAAKAYTTAJA],
    "lease_statistic": [
        UG.VALMISTELIJA,
        UG.SOPIMUSVALMISTELIJA,
        UG.SYOTTAJA,
        UG.PERINTALAKIMIES,
        UG.LASKUTTAJA,
        UG.PAAKAYTTAJA,
    ],
    "open_invoices": [UG.PERINTALAKIMIES, UG.LASKUTTAJA, UG.PAAKAYTTAJA],
    "rent_adjustments": [
        UG.VALMISTELIJA,
        UG.SOPIMUSVALMISTELIJA,
        UG.SYOTTAJA,
        UG.PERINTALAKIMIES,
        UG.LASKUTTAJA,
        UG.PAAKAYTTAJA,
    ],
    "rent_compare": [
        UG.VALMISTELIJA,
        UG.SOPIMUSVALMISTELIJA,
        UG.SYOTTAJA,
        UG.PERINTALAKIMIES,
        UG.LASKUTTAJA,
        UG.PAAKAYTTAJA,
    ],
    "rent_forecast": [
        UG.VALMISTELIJA,
        UG.SOPIMUSVALMISTELIJA,
        UG.SYOTTAJA,
        UG.PERINTALAKIMIES,
        UG.LASKUTTAJA,
        UG.PAAKAYTTAJA,
    ],
    "rent_type": [
        UG.VALMISTELIJA,
        UG.SOPIMUSVALMISTELIJA,
        UG.SYOTTAJA,
        UG.PERINTALAKIMIES,
        UG.LASKUTTAJA,
        UG.PAAKAYTTAJA,
    ],
    "rents_paid_contact": [UG.PERINTALAKIMIES, UG.LASKUTTAJA, UG.PAAKAYTTAJA],
    "reservations": [
        UG.VALMISTELIJA,
        UG.SOPIMUSVALMISTELIJA,
        UG.SYOTTAJA,
        UG.PERINTALAKIMIES,
        UG.LASKUTTAJA,
        UG.PAAKAYTTAJA,
    ],
}

# Reports that are removed can be added here. The permissions for these reports will be
# then deleted.
REMOVED_REPORTS = {"index_adjusted_rent_change"}


class Command(BaseCommand):
    help = "Sets report generation permissions for the predefined MVJ groups"

    def handle(self, *args, **options):
        report_slugs = set([report_class.slug for report_class in ENABLED_REPORTS])
        default_report_perms_keys = set(DEFAULT_REPORT_PERMS.keys())
        difference = default_report_perms_keys.difference(report_slugs)
        if difference:
            self.stderr.write(
                "Unknown reports in DEFAULT_REPORT_PERMS: {}".format(
                    ", ".join(difference)
                )
            )

        report_content_type, created = ContentType.objects.get_or_create(
            app_label="leasing", model="report"
        )

        for report_class in ENABLED_REPORTS:
            if report_class.slug not in DEFAULT_REPORT_PERMS.keys():
                self.stderr.write(
                    "Report {} ({}) not in DEFAULT_REPORT_PERMS. Skipping.".format(
                        report_class.__name__, report_class.slug
                    )
                )
                continue

            codename = "can_generate_report_{}".format(report_class.slug)
            name = "Can generate report {}".format(report_class.name)
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=report_content_type,
                defaults={"name": name},
            )

            groups = DEFAULT_REPORT_PERMS.get(report_class.slug)
            for group_id in groups:
                group = Group.objects.get(pk=group_id)
                group.permissions.add(permission)

        for report_slug in REMOVED_REPORTS:
            codename = "can_generate_report_{}".format(report_slug)
            try:
                permission = Permission.objects.get(codename=codename)
            except Permission.DoesNotExist:
                continue

            Group.permissions.through.objects.filter(permission=permission).delete()

            permission.delete()
