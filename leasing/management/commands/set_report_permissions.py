from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from leasing.report.viewset import ENABLED_REPORTS

# 1 Selailija
# 2 Valmistelija
# 3 Sopimusvalmistelija
# 4 Syöttäjä
# 5 Perintälakimies
# 6 Laskuttaja
# 7 Pääkäyttäjä

DEFAULT_REPORT_PERMS = {
    "collaterals": [5, 6, 7],
    "contact_rents": [2, 3, 4, 5, 6, 7],
    "decision_conditions": [2, 3, 4, 5, 6, 7],
    "extra_city_rent": [2, 3, 4, 5, 6, 7],
    "index_types": [2, 3, 4, 5, 6, 7],
    "invoice_payments": [5, 6, 7],
    "invoices_in_period": [5, 6, 7],
    "invoicing_review": [5, 6, 7],
    "laske_invoice_count": [5, 6, 7],
    "lease_count": [2, 3, 4, 5, 6, 7],
    "lease_invoicing_disabled": [5, 6, 7],
    "lease_statistic": [2, 3, 4, 5, 6, 7],
    "lease_statistic2": [2, 3, 4, 5, 6, 7],
    "open_invoices": [5, 6, 7],
    "rent_adjustments": [2, 3, 4, 5, 6, 7],
    "rent_compare": [2, 3, 4, 5, 6, 7],
    "rent_forecast": [2, 3, 4, 5, 6, 7],
    "rent_type": [2, 3, 4, 5, 6, 7],
    "rents_paid_contact": [5, 6, 7],
    "reservations": [2, 3, 4, 5, 6, 7],
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
