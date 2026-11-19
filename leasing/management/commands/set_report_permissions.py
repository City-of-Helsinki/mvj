from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from leasing.report.viewset import ENABLED_REPORTS
from utils.enums import AuthGroupId as AG

DEFAULT_REPORT_PERMS = {
    "collaterals": [AG.PERINTALAKIMIES, AG.LASKUTTAJA, AG.PAAKAYTTAJA],
    "contact_rents": [
        AG.VALMISTELIJA,
        AG.SOPIMUSVALMISTELIJA,
        AG.SYOTTAJA,
        AG.PERINTALAKIMIES,
        AG.LASKUTTAJA,
        AG.PAAKAYTTAJA,
    ],
    "decision_conditions": [
        AG.VALMISTELIJA,
        AG.SOPIMUSVALMISTELIJA,
        AG.SYOTTAJA,
        AG.PERINTALAKIMIES,
        AG.LASKUTTAJA,
        AG.PAAKAYTTAJA,
    ],
    "extra_city_rent": [
        AG.VALMISTELIJA,
        AG.SOPIMUSVALMISTELIJA,
        AG.SYOTTAJA,
        AG.PERINTALAKIMIES,
        AG.LASKUTTAJA,
        AG.PAAKAYTTAJA,
    ],
    "index_types": [
        AG.VALMISTELIJA,
        AG.SOPIMUSVALMISTELIJA,
        AG.SYOTTAJA,
        AG.PERINTALAKIMIES,
        AG.LASKUTTAJA,
        AG.PAAKAYTTAJA,
    ],
    "invoice_payments": [
        AG.VALMISTELIJA,
        AG.PERINTALAKIMIES,
        AG.LASKUTTAJA,
        AG.PAAKAYTTAJA,
    ],
    "invoices_in_period": [
        AG.VALMISTELIJA,
        AG.PERINTALAKIMIES,
        AG.LASKUTTAJA,
        AG.PAAKAYTTAJA,
    ],
    "invoicing_review": [
        AG.VALMISTELIJA,
        AG.PERINTALAKIMIES,
        AG.LASKUTTAJA,
        AG.PAAKAYTTAJA,
    ],
    "laske_invoice_count": [
        AG.VALMISTELIJA,
        AG.PERINTALAKIMIES,
        AG.LASKUTTAJA,
        AG.PAAKAYTTAJA,
    ],
    "invoice_details_and_forecast": [
        AG.VALMISTELIJA,
        AG.PERINTALAKIMIES,
        AG.LASKUTTAJA,
        AG.PAAKAYTTAJA,
    ],
    "lease_basis_of_rent": [
        AG.VALMISTELIJA,
        AG.SOPIMUSVALMISTELIJA,
        AG.SYOTTAJA,
        AG.PERINTALAKIMIES,
        AG.LASKUTTAJA,
        AG.PAAKAYTTAJA,
    ],
    "lease_count": [
        AG.VALMISTELIJA,
        AG.SOPIMUSVALMISTELIJA,
        AG.SYOTTAJA,
        AG.PERINTALAKIMIES,
        AG.LASKUTTAJA,
        AG.PAAKAYTTAJA,
    ],
    "lease_invoicing_disabled": [
        AG.VALMISTELIJA,
        AG.PERINTALAKIMIES,
        AG.LASKUTTAJA,
        AG.PAAKAYTTAJA,
    ],
    "lease_statistic": [
        AG.VALMISTELIJA,
        AG.SOPIMUSVALMISTELIJA,
        AG.SYOTTAJA,
        AG.PERINTALAKIMIES,
        AG.LASKUTTAJA,
        AG.PAAKAYTTAJA,
    ],
    "open_invoices": [
        AG.VALMISTELIJA,
        AG.PERINTALAKIMIES,
        AG.LASKUTTAJA,
        AG.PAAKAYTTAJA,
    ],
    "rent_adjustments": [
        AG.VALMISTELIJA,
        AG.SOPIMUSVALMISTELIJA,
        AG.SYOTTAJA,
        AG.PERINTALAKIMIES,
        AG.LASKUTTAJA,
        AG.PAAKAYTTAJA,
    ],
    "rent_compare": [
        AG.VALMISTELIJA,
        AG.SOPIMUSVALMISTELIJA,
        AG.SYOTTAJA,
        AG.PERINTALAKIMIES,
        AG.LASKUTTAJA,
        AG.PAAKAYTTAJA,
    ],
    "rent_forecast": [
        AG.VALMISTELIJA,
        AG.SOPIMUSVALMISTELIJA,
        AG.SYOTTAJA,
        AG.PERINTALAKIMIES,
        AG.LASKUTTAJA,
        AG.PAAKAYTTAJA,
    ],
    "rent_type": [
        AG.VALMISTELIJA,
        AG.SOPIMUSVALMISTELIJA,
        AG.SYOTTAJA,
        AG.PERINTALAKIMIES,
        AG.LASKUTTAJA,
        AG.PAAKAYTTAJA,
    ],
    "rents_paid_contact": [AG.PERINTALAKIMIES, AG.LASKUTTAJA, AG.PAAKAYTTAJA],
    "reservations": [
        AG.VALMISTELIJA,
        AG.SOPIMUSVALMISTELIJA,
        AG.SYOTTAJA,
        AG.PERINTALAKIMIES,
        AG.LASKUTTAJA,
        AG.PAAKAYTTAJA,
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
