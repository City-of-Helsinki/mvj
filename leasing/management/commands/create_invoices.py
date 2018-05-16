import datetime
from decimal import Decimal
from pprint import pprint

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from leasing.enums import InvoiceState, InvoiceType
from leasing.models import Invoice, Lease, ReceivableType
from leasing.models.utils import fix_amount_for_overlap, get_range_overlap_and_remainder, subtract_ranges_from_ranges


class Command(BaseCommand):
    help = 'A Bogus Invoice creator'

    def handle(self, *args, **options):
        today = datetime.date.today()
        # today = today.replace(year=2018, month=3, day=1)
        today = today.replace(year=2016, month=12, day=1)
        # today = today.replace(month=3, day=1)

        # TODO: Make configurable
        receivable_type_rent = ReceivableType.objects.get(pk=1)

        if today.day != 1:
            # TODO: allow override
            raise CommandError('Invoices should only be generated on the first day of the month')

        start_of_next_month = today.replace(day=1) + relativedelta(months=1)
        end_of_next_month = start_of_next_month + relativedelta(day=31)

        self.stdout.write('Finding leases with due dates between {} and {}\n'.format(start_of_next_month,
                                                                                     end_of_next_month))

        leases = Lease.objects.filter(
            # is_invoicing_enabled=True,
        ).filter(
            Q(Q(end_date=None) | Q(end_date__gte=today)) &
            Q(Q(start_date=None) | Q(start_date__lte=today))
        )

        for lease in leases:
            if lease.id != 19:
                continue

            self.stdout.write('Lease #{} {}:'.format(lease.id, lease.identifier))
            lease_due_dates = lease.get_due_dates_for_period(start_of_next_month, end_of_next_month)
            if not lease_due_dates:
                self.stdout.write(' No due dates in the period\n\n')
                continue

            self.stdout.write(' Due dates {}'.format(', '.join([dd.strftime('%Y-%m-%d') for dd in lease_due_dates])))

            range_filter = Q()
            for lease_due_date in lease_due_dates:
                range_filter |= Q(
                    Q(Q(end_date=None) | Q(end_date__gte=lease_due_date)) &
                    Q(Q(start_date=None) | Q(start_date__lte=lease_due_date))
                )

            for lease_due_date in lease_due_dates:
                rent_amount = Decimal(0)
                self.stdout.write(' Due date {}'.format(lease_due_date))

                # TODO: multiple rents and billing periods
                for rent in lease.rents.filter(range_filter):
                    self.stdout.write('  Rent #{}'.format(rent.id))
                    billing_period = rent.get_billing_period_from_due_date(lease_due_date)
                    self.stdout.write('   Billing period {} - {}'.format(
                        billing_period[0].strftime('%Y-%m-%d'), billing_period[1].strftime('%Y-%m-%d')))
                    rent_amount += rent.get_amount_for_date_range(*billing_period)

                self.stdout.write('  Rent amount {}'.format(round(rent_amount, 2)))

                range_filter = Q(
                    Q(Q(tenantcontact__end_date=None) | Q(tenantcontact__end_date__gte=billing_period[0])) &
                    Q(Q(tenantcontact__start_date=None) | Q(tenantcontact__start_date__lte=billing_period[1]))
                )

                shares = {}
                for tenant in lease.tenants.filter(range_filter).distinct():
                    self.stdout.write('  Tenant #{} share {}/{}'.format(
                        tenant.id, tenant.share_numerator, tenant.share_denominator))

                    tenant_tenantcontacts = tenant.get_tenant_tenantcontacts(billing_period[0], billing_period[1])
                    for tenant_tenantcontact in tenant_tenantcontacts:
                        self.stdout.write('   Tenant contact: {} dates: {} - {}'.format(
                            tenant_tenantcontact.contact, tenant_tenantcontact.start_date, tenant_tenantcontact.end_date))

                    billing_tenantcontacts = tenant.get_billing_tenantcontacts(billing_period[0], billing_period[1])
                    if not billing_tenantcontacts:
                        self.stdout.write('***** NO BILLING CONTACT. SKIPPING.')
                        continue

                    (tenant_overlap, tenant_remainders) = get_range_overlap_and_remainder(
                        billing_period[0], billing_period[1], *tenant_tenantcontacts[0].date_range)

                    if not tenant_overlap:
                        self.stdout.write('   No overlap with this billing period. Error?')
                        continue

                    # print("TENANT_OVERLAP: ", tenant_overlap)

                    for billing_tenantcontact in billing_tenantcontacts:
                        self.stdout.write('   Billing contact: {} ({}) dates: {} - {}'.format(
                            billing_tenantcontact.contact, billing_tenantcontact.type, billing_tenantcontact.start_date,
                            billing_tenantcontact.end_date))

                        (billing_overlap, billing_remainders) = get_range_overlap_and_remainder(
                            tenant_overlap[0], tenant_overlap[1], *billing_tenantcontact.date_range)

                        if not billing_overlap:
                            continue

                        # print("BILLING_OVERLAP: ", billing_overlap)
                        # print("BILLING_REMAINDERS: ", billing_remainders)

                        if billing_tenantcontact.contact not in shares:
                            shares[billing_tenantcontact.contact] = {}

                        if tenant not in shares[billing_tenantcontact.contact]:
                            shares[billing_tenantcontact.contact][tenant] = []

                        shares[billing_tenantcontact.contact][tenant].append(billing_overlap)

                    ranges_for_billing_contacts = []
                    for billing_contact, tenant_overlaps in shares.items():
                        if tenant in tenant_overlaps:
                            ranges_for_billing_contacts.extend(tenant_overlaps[tenant])

                    leftover_ranges = subtract_ranges_from_ranges([billing_period], ranges_for_billing_contacts)

                    if leftover_ranges:
                        if tenant_tenantcontacts[0].contact not in shares:
                            shares[tenant_tenantcontacts[0].contact] = {
                                tenant: [],
                            }
                        shares[tenant_tenantcontacts[0].contact][tenant].extend(leftover_ranges)

                pprint(shares)

                self.stdout.write('')

                for contact, share in shares.items():
                    for tenant, overlaps in share.items():
                        overlap_amount = Decimal(0)
                        for overlap in overlaps:
                            overlap_amount += fix_amount_for_overlap(
                                rent_amount, overlap, subtract_ranges_from_ranges([billing_period], [overlap]))

                        share_amount = round(overlap_amount * Decimal(
                            tenant.share_numerator / tenant.share_denominator), 2)

                        self.stdout.write('  Share for contact {} {} ({})'.format(contact, share_amount, tenant))
                        self.stdout.write('  Creating an invoice')

                        # TODO: Check if invoice already created
                        invoice = Invoice.objects.create(
                            type=InvoiceType.CHARGE,
                            lease=lease,
                            recipient=contact,
                            due_date=lease_due_date,
                            invoicing_date=today,
                            receivable_type=receivable_type_rent,
                            state=InvoiceState.OPEN,
                            billing_period_start_date=billing_period[0],
                            billing_period_end_date=billing_period[1],
                            total_amount=rent_amount,
                            share_numerator=tenant.share_numerator,
                            share_denominator=tenant.share_denominator,
                            billed_amount=share_amount,
                            outstanding_amount=share_amount,
                            paid_amount=None,
                        )

                self.stdout.write('')
