import datetime
from decimal import ROUND_HALF_UP, Decimal

import xlsxwriter
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

# from leasing.enums import IndexType, InvoiceState, InvoiceType, LeaseState, RentCycle, RentType
# from leasing.models import Lease, PayableRent, ReceivableType
from leasing.enums import LeaseState, RentCycle, RentType
from leasing.models import Lease, PayableRent

known_errors = {
    ('A1154-878', Decimal('19364.80')): 'known error in the old system',
    ('A1154-878', Decimal('11830.54')): 'known error in the old system',
}


class Command(BaseCommand):
    help = 'Import data from the old MVJ'

    def handle(self, *args, **options):  # NOQA
        today = timezone.now().date()

        leases = Lease.objects.filter(state=LeaseState.LEASE).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=today)
        ).order_by('start_date')

        workbook = xlsxwriter.Workbook('compare_payable_rents.xlsx')
        worksheet = workbook.add_worksheet()

        worksheet.freeze_panes(1, 0)
        worksheet.set_column(1, 1, 5)
        worksheet.set_column(2, 2, 13)
        worksheet.set_column(3, 3, 13)
        worksheet.set_column(4, 4, 13)

        number = workbook.add_format({'num_format': '0.00'})
        red = workbook.add_format({'font_color': '#ff0000'})
        green = workbook.add_format({'font_color': '#008000'})
        red_number = workbook.add_format({'num_format': '0.00', 'font_color': '#ff0000'})
        green_number = workbook.add_format({'num_format': '0.00', 'font_color': '#008000'})

        row = 0
        worksheet.write(row, 0, "Lease")
        worksheet.write(row, 1, "Year")
        worksheet.write(row, 2, "Payable rent")
        worksheet.write(row, 3, "Calculated")
        worksheet.write(row, 4, "Difference")
        worksheet.write(row, 5, "Correct")
        worksheet.write(row, 6, "Wrong")
        row += 1

        for lease in leases:
            self.stdout.write('Lease #{} {} '.format(lease.id, lease))

            rent = lease.rents.first()
            if not rent:
                self.stdout.write(' No rent. Skipping')
                continue

            if rent.type == RentType.MANUAL:
                self.stdout.write(" Skipping rent type MANUAL")
                continue

            # Year rent...
            payable_rents = PayableRent.objects.filter(rent=rent, start_date__year=2019).order_by('start_date')
            if not payable_rents:
                self.stdout.write(' No payable rents. Skipping')
                continue

            for payable_rent in payable_rents:
                year = payable_rent.start_date.year
                if rent.cycle == RentCycle.JANUARY_TO_DECEMBER:
                    year_start = datetime.date(year=year, month=1, day=1)
                    year_end = datetime.date(year=year, month=12, day=31)
                else:
                    year_start = datetime.date(year=year, month=4, day=1)
                    year_end = datetime.date(year=year + 1, month=3, day=31)

                # if rent.index_type in (IndexType.TYPE_1, IndexType.TYPE_2, IndexType.TYPE_3, IndexType.TYPE_4):
                #     self.stdout.write(" Skipping indextype 1-4")
                #     continue

                try:
                    calculated_amount = rent.get_amount_for_date_range(year_start, year_end).quantize(
                        Decimal('.01'), rounding=ROUND_HALF_UP)
                except AssertionError:
                    self.stdout.write(" Assertion error")
                    worksheet.write(row, 0, lease.get_identifier_string())
                    worksheet.write(row, 1, year)
                    worksheet.write(row, 2, payable_rent.amount, number)
                    worksheet.write(row, 4, "Assertion error", red)
                    worksheet.write(row, 6, "x", red)
                    row += 1
                    continue
                except TypeError as e:
                    self.stdout.write(str(e))
                    worksheet.write(row, 0, lease.get_identifier_string())
                    worksheet.write(row, 1, year)
                    worksheet.write(row, 2, payable_rent.amount, number)
                    worksheet.write(row, 4, str(e), red)
                    worksheet.write(row, 6, "x", red)
                    row += 1
                    continue
                except Exception as e:
                    self.stdout.write(str(e))
                    worksheet.write(row, 0, lease.get_identifier_string())
                    worksheet.write(row, 1, year)
                    worksheet.write(row, 2, payable_rent.amount, number)
                    worksheet.write(row, 4, str(e), red)
                    worksheet.write(row, 6, "x", red)
                    row += 1
                    continue

                color = green_number

                difference = calculated_amount - payable_rent.amount

                if abs(difference) > Decimal('0.05'):
                    color = red_number
                    self.stdout.write(' Payable rent amount year {}: {}'.format(year, payable_rent.amount))
                    self.stdout.write(' Calculated amount            : {} {}'.format(
                        calculated_amount,
                        ' matches' if payable_rent.amount == calculated_amount else ' MISMATCH'
                    ))
                    worksheet.write(row, 6, "x", red)
                else:
                    worksheet.write(row, 5, "x", green)

                worksheet.write(row, 0, lease.get_identifier_string())
                worksheet.write(row, 1, year)
                worksheet.write(row, 2, payable_rent.amount, number)
                worksheet.write(row, 3, calculated_amount, number)
                worksheet.write(row, 4, difference, color)
                row += 1

        row += 1
        worksheet.write(row, 0, 'Total count')
        worksheet.write(row, 1, '=COUNTA(A2:A{})'.format(row-1))

        row += 1
        worksheet.write(row, 0, 'Correct')
        worksheet.write(row, 1, '=COUNTA(F2:F{})'.format(row - 1))

        row += 1
        worksheet.write(row, 0, 'Wrong')
        worksheet.write(row, 1, '=COUNTA(G2:G{})'.format(row - 1))
        workbook.close()

        # Invoices...
        # for invoice in lease.invoices.filter(type=InvoiceType.CHARGE, state=InvoiceState.PAID).order_by(
        #         'billing_period_start_date'):
        #     calculated_amount = round(
        #         rent.get_amount_for_date_range(invoice.billing_period_start_date, invoice.billing_period_end_date),
        #         2)
        #     extra_texts = []
        #     if invoice.total_amount != calculated_amount and \
        #             round(invoice.total_amount) == round(calculated_amount):
        #         extra_texts.append('but close enough')
        #
        #     if (str(lease.identifier), invoice.total_amount) in known_errors:
        #         extra_texts.append(known_errors[(str(lease.identifier), invoice.total_amount)])
        #
        #     self.stdout.write(' Invoice #{} {} - {} amount: {} calculated amount: {} {} {}'.format(
        #         invoice.id,
        #         invoice.billing_period_start_date,
        #         invoice.billing_period_end_date,
        #         invoice.total_amount,
        #         calculated_amount,
        #         'MISMATCH' if invoice.total_amount != calculated_amount else '',
        #         ' '.join(extra_texts),
        #     ))

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
