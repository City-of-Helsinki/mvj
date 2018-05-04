import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand

from leasing.enums import InvoiceState, InvoiceType
from leasing.models import Lease, PayableRent, ReceivableType

known_errors = {
    ('A1154-878', Decimal('19364.80')): 'known error in the old system',
    ('A1154-878', Decimal('11830.54')): 'known error in the old system',
}

class Command(BaseCommand):
    help = 'Import data from the old MVJ'

    def handle(self, *args, **options):
        leases = Lease.objects.all().order_by('start_date')
        # leases = Lease.objects.filter(id__in=[11]).order_by('start_date')

        for lease in leases:
            # from_year = lease.start_date.year
            # to_year = datetime.date.today().year
            # year_range = range(from_year, to_year)

            self.stdout.write('Lease #{} {} '.format(lease.id, lease))

            rent = lease.rents.first()

            # Year rent...
            # for year in year_range:
            #     year_start = datetime.date(year=year, month=1, day=1)
            #     year_end = datetime.date(year=year, month=12, day=31)
            #
            #     payable_rents = PayableRent.objects.filter(rent=rent, end_date__year=year)
            #     for payable_rent in payable_rents:
            #         # calculated_amount = round(rent.get_amount_for_date_range(
            #         #     payable_rent.start_date, payable_rent.end_date), 2)
            #         calculated_amount = round(rent.get_amount_for_date_range(
            #             year_start, year_end), 2)
            #
            #         self.stdout.write('  Payable rent amount: {}'.format(payable_rent.amount))
            #         self.stdout.write('  Calculated amount: {} {}'.format(
            #             calculated_amount,
            #             ' matches' if payable_rent.amount == calculated_amount else ' MISMATCH'
            #         ))

            for invoice in lease.invoices.filter(type=InvoiceType.CHARGE, receivable_type_id=1,
                                                 state=InvoiceState.PAID).order_by('billing_period_start_date'):
                calculated_amount = round(
                    rent.get_amount_for_date_range(invoice.billing_period_start_date, invoice.billing_period_end_date),
                    2)
                extra_texts = []
                if invoice.total_amount != calculated_amount and \
                        round(invoice.total_amount) == round(calculated_amount):
                    extra_texts.append('but close enough')

                if (str(lease.identifier), invoice.total_amount) in known_errors:
                    extra_texts.append(known_errors[(str(lease.identifier), invoice.total_amount)])

                self.stdout.write(' Invoice #{} {} - {} amount: {} calculated amount: {} {} {}'.format(
                    invoice.id,
                    invoice.billing_period_start_date,
                    invoice.billing_period_end_date,
                    invoice.total_amount,
                    calculated_amount,
                    'MISMATCH' if invoice.total_amount != calculated_amount else '',
                    ' '.join(extra_texts),
                ))

            # for rent in lease.rents.all():
            #     self.stdout.write(' Rent #{} {}'.format(rent.id, rent.type))
            #
            #     for year in year_range:
            #         self.stdout.write('  Year {}'.format(year))
            #         year_start = datetime.date(year=year, month=1, day=1)
            #         year_end = datetime.date(year=year, month=12, day=31)
            #
            #         self.stdout.write('  Period {} - {}'.format(year_start, year_end))
            #
            #         try:
            #             payable_rents = PayableRent.objects.filter(rent=rent, end_date__year=year)
            #             for payable_rent in payable_rents:
            #                 calculated_amount = round(rent.get_amount_for_date_range(
            #                     payable_rent.start_date, payable_rent.end_date), 2)
            #
            #                 self.stdout.write('  Payable rent amount: {}'.format(payable_rent.amount))
            #                 self.stdout.write('  Calculated amount: {} {}'.format(
            #                     calculated_amount,
            #                     ' matches' if payable_rent.amount == calculated_amount else ' MISMATCH'
            #                 ))
            #         except PayableRent.DoesNotExist:
            #             self.stdout.write('  No PayableRent for this period')
