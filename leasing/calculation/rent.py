from decimal import ROUND_HALF_UP, Decimal

from leasing.enums import InvoiceState
from leasing.models.invoice import InvoiceType, ReceivableType
from leasing.models.utils import combine_ranges, fix_amount_for_overlap, subtract_ranges_from_ranges


class RentCalculation:
    def __init__(self, lease=None, start_date=None, end_date=None):
        self.lease = lease
        self.start_date = start_date
        self.end_date = end_date

    def determine_payable_rents_and_periods(self, start_date, end_date):
        lease_due_dates = self.lease.get_due_dates_for_period(start_date, end_date)
        if not lease_due_dates:
            # TODO
            return {}

        amounts_for_billing_periods = {}

        for lease_due_date in lease_due_dates:
            for rent in self.lease.get_active_rents_on_period(start_date, end_date):
                billing_period = rent.get_billing_period_from_due_date(lease_due_date)

                if not billing_period:
                    continue

                if billing_period not in amounts_for_billing_periods:
                    amounts_for_billing_periods[billing_period] = {
                        'due_date': lease_due_date,
                        'amount': Decimal(0),
                        'explanations': [],
                    }

                (this_amount, explanation) = rent.get_amount_for_date_range(*billing_period, explain=True)

                amounts_for_billing_periods[billing_period]['amount'] += this_amount
                amounts_for_billing_periods[billing_period]['explanations'].append(explanation)

        return amounts_for_billing_periods

    def calculate_invoices(self):
        # TODO: Make configurable
        receivable_type_rent = ReceivableType.objects.get(pk=1)

        rents = self.determine_payable_rents_and_periods(self.start_date, self.end_date)

        invoice_data = []

        for billing_period, period_rent in rents.items():
            billing_period_invoices = []
            rent_amount = period_rent['amount']

            shares = self.lease.get_tenant_shares_for_period(*billing_period)
            # TODO: leftover ranges?

            for contact, share in shares.items():
                billable_amount = Decimal(0)
                contact_ranges = []
                invoice_row_data = []

                for tenant, overlaps in share.items():
                    overlap_amount = Decimal(0)
                    for overlap in overlaps:
                        overlap_amount += fix_amount_for_overlap(
                            rent_amount, overlap, subtract_ranges_from_ranges([billing_period], [overlap]))

                        share_amount = Decimal(
                            overlap_amount * Decimal(tenant.share_numerator / tenant.share_denominator)
                        ).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)

                        billable_amount += share_amount

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

                total_contact_period_amount = Decimal(total_contact_period_amount).quantize(Decimal('.01'),
                                                                                            rounding=ROUND_HALF_UP)

                invoice_datum = {
                    'type': InvoiceType.CHARGE,
                    'lease': self.lease,
                    'recipient': contact,
                    'due_date': period_rent['due_date'],
                    'billing_period_start_date': billing_period[0],
                    'billing_period_end_date': billing_period[1],
                    'total_amount': total_contact_period_amount,
                    'billed_amount': billable_amount,
                    'rows': invoice_row_data,
                    'explanations': period_rent['explanations'],
                    'state': InvoiceState.OPEN,
                }

                billing_period_invoices.append(invoice_datum)

            invoice_data.append(billing_period_invoices)

        return invoice_data
