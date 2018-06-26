import datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from sequences import get_next_value

from leasing.enums import InvoiceState, InvoiceType
from leasing.models import Invoice, Lease, ReceivableType
from leasing.models.invoice import InvoiceRow, InvoiceSet
from leasing.models.utils import (
    combine_ranges, fix_amount_for_overlap, get_range_overlap_and_remainder, subtract_ranges_from_ranges)


class Command(BaseCommand):
    help = 'A Bogus Invoice creator'

    def handle(self, *args, **options):  # noqa: C901 'Command.handle' is too complex TODO
        today = datetime.date.today()
        # today = today.replace(year=2018, month=3, day=1)
        # today = today.replace(year=2016, month=12, day=1)  # Y11...
        # today = today.replace(year=2017, month=9, day=1)  # A1134-430
        # today = today.replace(month=3, day=1)
        today = today.replace(day=1)

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
            # if lease.id != 19:  # Y1111-1
            #     continue
            # if lease.id != 10:  # A1134-430
            #     continue

            self.stdout.write('Lease #{} {}:'.format(lease.id, lease.identifier))
            lease_due_dates = lease.get_due_dates_for_period(start_of_next_month, end_of_next_month)
            if not lease_due_dates:
                self.stdout.write(' No due dates in the period\n\n')
                continue

            self.stdout.write(' Due dates {}'.format(', '.join([dd.strftime('%Y-%m-%d') for dd in lease_due_dates])))

            for lease_due_date in lease_due_dates:
                rent_amount = Decimal(0)
                self.stdout.write(' Due date {}'.format(lease_due_date))

                rent_range_filter = Q(
                    (Q(end_date=None) | Q(end_date__gte=lease_due_date)) &
                    (Q(start_date=None) | Q(start_date__lte=lease_due_date))
                )

                # TODO: multiple rents and billing periods
                for rent in lease.rents.filter(rent_range_filter):
                    self.stdout.write('  Rent #{}'.format(rent.id))
                    billing_period = rent.get_billing_period_from_due_date(lease_due_date)
                    self.stdout.write('   Billing period {} - {}'.format(
                        billing_period[0].strftime('%Y-%m-%d'), billing_period[1].strftime('%Y-%m-%d')))
                    rent_amount += rent.get_amount_for_date_range(*billing_period)

                self.stdout.write('  Rent amount {}'.format(round(rent_amount, 2)))

                tenant_range_filter = Q(
                    Q(Q(tenantcontact__end_date=None) | Q(tenantcontact__end_date__gte=billing_period[0])) &
                    Q(Q(tenantcontact__start_date=None) | Q(tenantcontact__start_date__lte=billing_period[1]))
                )

                shares = {}
                for tenant in lease.tenants.filter(tenant_range_filter).distinct():
                    self.stdout.write('  Tenant #{} share {}/{}'.format(
                        tenant.id, tenant.share_numerator, tenant.share_denominator))

                    tenant_tenantcontacts = tenant.get_tenant_tenantcontacts(billing_period[0], billing_period[1])
                    for tenant_tenantcontact in tenant_tenantcontacts:
                        self.stdout.write('   Tenant contact: {} dates: {} - {}'.format(
                            tenant_tenantcontact.contact, tenant_tenantcontact.start_date, tenant_tenantcontact.end_date
                        ))

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

                self.stdout.write('')

                invoiceset = None
                if len(shares.items()) > 1:
                    try:
                        invoiceset = InvoiceSet.objects.get(
                            lease=lease,
                            billing_period_start_date=billing_period[0],
                            billing_period_end_date=billing_period[1],
                        )
                        self.stdout.write('  Invoiceset already exists.')
                    except InvoiceSet.DoesNotExist as e:
                        invoiceset = InvoiceSet.objects.create(
                            lease=lease,
                            billing_period_start_date=billing_period[0],
                            billing_period_end_date=billing_period[1],
                        )

                for contact, share in shares.items():
                    self.stdout.write('  Shares for contact {}'.format(contact))

                    billable_amount = Decimal(0)
                    contact_ranges = []
                    invoice_row_data = []

                    for tenant, overlaps in share.items():
                        self.stdout.write('   Tenant #{}'.format(tenant.id))

                        overlap_amount = Decimal(0)
                        for overlap in overlaps:
                            overlap_amount += fix_amount_for_overlap(
                                rent_amount, overlap, subtract_ranges_from_ranges([billing_period], [overlap]))

                            share_amount = round(overlap_amount * Decimal(
                                tenant.share_numerator / tenant.share_denominator), 2)

                            billable_amount += share_amount

                            self.stdout.write('   Period {} - {} = {:.2f} / {:.2f}'.format(
                                overlap[0], overlap[1], share_amount, overlap_amount))

                            contact_ranges.append(overlap)
                            invoice_row_data.append({
                                'tenant': tenant,
                                'receivable_type': receivable_type_rent,
                                'billing_period_start_date': overlap[0],
                                'billing_period_end_date': overlap[1],
                                'amount': share_amount,
                            })

                    combined_contact_ranges = combine_ranges(contact_ranges)

                    total_contact_period_amount = Decimal(0)
                    for combined_contact_range in combined_contact_ranges:
                        total_contact_period_amount += fix_amount_for_overlap(
                            rent_amount, combined_contact_range, subtract_ranges_from_ranges(
                                [billing_period], [combined_contact_range]))

                    self.stdout.write('  Total: {:.2f} / {:.2f}'.format(billable_amount, total_contact_period_amount))

                    try:
                        invoice = Invoice.objects.get(
                            type=InvoiceType.CHARGE,
                            lease=lease,
                            recipient=contact,
                            due_date=lease_due_date,
                            billing_period_start_date=billing_period[0],
                            billing_period_end_date=billing_period[1],
                            total_amount=round(total_contact_period_amount, 2),
                            generated=True,
                            invoiceset=invoiceset,
                        )
                        self.stdout.write('  Invoice already exists. Invoice id {}. Number {}'.format(
                            invoice.id, invoice.number))
                    except Invoice.DoesNotExist as e:
                        with transaction.atomic():
                            invoice = Invoice.objects.create(
                                type=InvoiceType.CHARGE,
                                lease=lease,
                                number=get_next_value('invoice_numbers', initial_value=1000000),
                                recipient=contact,
                                due_date=lease_due_date,
                                invoicing_date=today,
                                state=InvoiceState.OPEN,
                                billing_period_start_date=billing_period[0],
                                billing_period_end_date=billing_period[1],
                                total_amount=round(total_contact_period_amount, 2),
                                billed_amount=billable_amount,
                                outstanding_amount=billable_amount,
                                generated=True,
                                invoiceset=invoiceset,
                            )

                            for invoice_row_datum in invoice_row_data:
                                invoice_row_datum['invoice'] = invoice
                                InvoiceRow.objects.create(**invoice_row_datum)

                        self.stdout.write('  Invoice created. Invoice id {}. Number {}'.format(
                            invoice.id, invoice.number))
                    except Invoice.MultipleObjectsReturned:
                        self.stdout.write('  Warning! Multiple invoices already exist. Not creating a new invoice.')

                self.stdout.write('')
