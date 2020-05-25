from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

# 1 Selailija
# 2 Valmistelija
# 3 Sopimusvalmistelija
# 4 Syöttäjä
# 5 Perintälakimies
# 6 Laskuttaja
# 7 Pääkäyttäjä

DEFAULT_REPORT_PERMS = {
    "invoice_payments": [5, 6, 7],
    "invoices_in_period": [5, 6, 7],
    "laske_invoice_count": [5, 6, 7],
    "money_collaterals": [5, 6, 7],
    "open_invoices": [5, 6, 7],
    "decision_conditions": [2, 3, 4, 5, 6, 7],
    "extra_city_rent": [2, 3, 4, 5, 6, 7],
    "lease_invoicing_disabled": [5, 6, 7],
    "lease_statistic": [2, 3, 4, 5, 6, 7],
    "lease_count": [2, 3, 4, 5, 6, 7],
    "rent_forecast": [2, 3, 4, 5, 6, 7],
    "reservations": [2, 3, 4, 5, 6, 7],
}


class Command(BaseCommand):
    help = "Sets predefined model permissions for the predefined MVJ groups"

    def handle(self, *args, **options):
        ctype, created = ContentType.objects.get_or_create(
            app_label="leasing", model="report"
        )
        for report in DEFAULT_REPORT_PERMS:

            codename = "can_generate_report_{}".format(report)
            name = "Can generate report {}".format(report)
            permission, created = Permission.objects.get_or_create(
                codename=codename, name=name, content_type=ctype
            )

            groups = DEFAULT_REPORT_PERMS.get(report)
            for group_id in groups:
                group = Group.objects.get(pk=group_id)
                group.permissions.add(permission)
