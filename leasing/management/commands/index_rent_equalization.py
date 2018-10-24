import datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from leasing.enums import InvoiceState, InvoiceType
from leasing.models import Invoice
from leasing.models.invoice import InvoiceRow


class Command(BaseCommand):
    help = 'Creates credit notes or invoices if index number has changed after the invoices are sent'

    def handle(self, *args, **options):  # noqa: C901 'Command.handle' is too complex TODO
        today = datetime.date.today()
        today = today.replace(year=2018, month=3, day=1)

        december_last_year = datetime.date(year=today.year - 1, month=12, day=1)

        self.stdout.write('Finding invoices with invoicing dates between {} and {}\n'.format(
            december_last_year, today))

        # Find invoices that were created before the new index was known
        invoices = Invoice.objects.filter(
            invoicing_date__range=[december_last_year, today],
            type=InvoiceType.CHARGE,
            generated=True
        ).select_related('lease')

        sent_invoice_data = {}
        for invoice in invoices:
            billing_period = (invoice.billing_period_start_date, invoice.billing_period_end_date)
            self.stdout.write('Invoice #{} Lease {} Billing period {} - {}'.format(
                invoice.id, invoice.lease.identifier, billing_period[0], billing_period[1]))

            if invoice.lease not in sent_invoice_data:
                sent_invoice_data[invoice.lease] = {
                    'invoices': [],
                    'billing_periods': {},
                }

            sent_invoice_data[invoice.lease]['invoices'].append(invoice)
            if billing_period not in sent_invoice_data[invoice.lease]['billing_periods']:
                sent_invoice_data[invoice.lease]['billing_periods'][billing_period] = Decimal(0)

            if invoice.type == InvoiceType.CHARGE:
                sent_invoice_data[invoice.lease]['billing_periods'][billing_period] += invoice.billed_amount
            elif invoice.type == InvoiceType.CREDIT_NOTE:
                sent_invoice_data[invoice.lease]['billing_periods'][billing_period] -= invoice.billed_amount

        for lease, data in sent_invoice_data.items():
            for billing_period, invoiced_rent_amount in data['billing_periods'].items():
                (rent_amount, explanations) = lease.get_rent_amount_and_explations_for_period(*billing_period)

                if rent_amount == invoiced_rent_amount:
                    self.stdout.write(' Rent amount is the same ({}) no need to equalize.'.format(rent_amount))
                    continue

                rent_difference = rent_amount - invoiced_rent_amount

                self.stdout.write(' Rent amount is not the same. {} - {} = {}.'.format(
                    rent_amount, invoiced_rent_amount, rent_difference))

                new_due_date = today + relativedelta(days=settings.MVJ_DUE_DATE_OFFSET_DAYS)

                amounts_for_billing_periods = {
                    billing_period: {
                        'due_date': new_due_date,
                        'amount': abs(rent_difference),
                        'explanations': [],
                    }
                }

                new_invoice_data = lease.calculate_invoices(amounts_for_billing_periods)

                for period_invoice_data in new_invoice_data:
                    for invoice_data in period_invoice_data:
                        invoice_data.pop('explanations')

                        # The new new rent is smaller
                        if rent_difference < Decimal(0):
                            invoice_data['type'] = InvoiceType.CREDIT_NOTE

                        original_invoice = None
                        for sent_invoice in data['invoices']:
                            if sent_invoice.is_same_recipient_and_tenants(invoice_data):
                                original_invoice = sent_invoice

                        if original_invoice is None:
                            self.stdout.print(' Original invoice not found')
                            continue

                        invoice_data['generated'] = True
                        invoice_data['invoiceset'] = original_invoice.invoiceset
                        invoice_row_data = invoice_data.pop('rows')

                        try:
                            invoice = Invoice.objects.get(**invoice_data)
                            self.stdout.write(
                                '  Invoice already exists. Invoice id {}. Number {}'.format(invoice.id, invoice.number))
                        except Invoice.DoesNotExist:
                            with transaction.atomic():
                                # invoice_data['number'] = get_next_value('invoice_numbers', initial_value=1000000)
                                invoice_data['invoicing_date'] = today

                                if InvoiceType.CHARGE:
                                    invoice_data['outstanding_amount'] = invoice_data['billed_amount']

                                invoice = Invoice.objects.create(**invoice_data)

                                for invoice_row_datum in invoice_row_data:
                                    invoice_row_datum['invoice'] = invoice
                                    InvoiceRow.objects.create(**invoice_row_datum)

                                if invoice_data['type'] == InvoiceType.CREDIT_NOTE:
                                    original_invoice.state = InvoiceState.PARTIALLY_REFUNDED
                                    original_invoice.save()

                            self.stdout.write(
                                '  Invoice created. Invoice id {}. Number {}'.format(invoice.id, invoice.number))
                        except Invoice.MultipleObjectsReturned:
                            self.stdout.write('  Warning! Multiple invoices already exist. Not creating a new invoice.')

            self.stdout.write('')
