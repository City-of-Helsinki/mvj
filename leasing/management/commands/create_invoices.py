from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from leasing.models import Invoice, Lease


class Command(BaseCommand):
    help = 'A Bogus Invoice creator'

    def handle(self, *args, **options):
        now = timezone.localtime(timezone.now())

        leases = Lease.objects.filter(is_billing_enabled=True)

        for lease in leases:
            next_billing_period = lease.get_next_billing_period_for_date(now.date())

            amount = lease.get_rent_amount_for_period(*next_billing_period)

            shares = {}
            for tenant in lease.tenants.all():
                if tenant.get_billing_contact() not in shares:
                    shares[tenant.get_billing_contact()] = {
                        'share': 0,
                        'tenants': []
                    }

                shares[tenant.get_billing_contact()]['share'] += tenant.share
                shares[tenant.get_billing_contact()]['tenants'].append(tenant)

            for contact, share in shares.items():
                invoice_exists = Invoice.objects.filter(
                    period_start_date=next_billing_period[0],
                    period_end_date=next_billing_period[1],
                    billing_contact=contact,
                ).count()

                if invoice_exists:
                    continue

                invoice = Invoice.objects.create(
                    period_start_date=next_billing_period[0],
                    period_end_date=next_billing_period[1],
                    due_date=next_billing_period[0],
                    amount=amount * Decimal(share['share']),
                    billing_contact=contact,
                )

                invoice.tenants.set(share['tenants'])

                invoice.create_reference_number()
