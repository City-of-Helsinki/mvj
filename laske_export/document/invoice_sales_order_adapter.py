from decimal import ROUND_HALF_UP, Decimal

from dateutil.relativedelta import relativedelta
from django.conf import settings

from leasing.enums import InvoiceType, RentCycle
from leasing.models.utils import get_next_business_day, is_business_day

from .sales_order import BillingParty1, LineItem, OrderParty


class InvoiceSalesOrderAdapter:
    def __init__(self, invoice=None, sales_order=None, receivable_type_rent=None):
        self.invoice = invoice
        self.sales_order = sales_order
        self.receivable_type_rent = receivable_type_rent

    def get_bill_text(self):
        if self.invoice.billing_period_start_date and self.invoice.billing_period_end_date:
            invoice_year = self.invoice.billing_period_start_date.year

            # TODO: Which rent
            rent = self.invoice.lease.get_active_rents_on_period(self.invoice.billing_period_start_date,
                                                                 self.invoice.billing_period_end_date).first()
        else:
            invoice_year = self.invoice.invoicing_date.year

            rent = self.invoice.lease.get_active_rents_on_period(self.invoice.invoicing_date,
                                                                 self.invoice.invoicing_date).first()

        rent_calculation = self.invoice.lease.calculate_rent_amount_for_year(invoice_year)
        year_rent = rent_calculation.get_total_amount()

        real_property_identifier = ''
        address = ''

        first_lease_area = self.invoice.lease.lease_areas.first()
        if first_lease_area:
            real_property_identifier = first_lease_area.identifier
            lease_area_address = first_lease_area.addresses.first()
            if lease_area_address:
                address = lease_area_address.address

        bill_texts = []
        row1 = 'Vuokraustunnus: {lease_identifier}  '.format(
            lease_identifier=self.invoice.lease.get_identifier_string())

        if self.invoice.billing_period_start_date and self.invoice.billing_period_end_date:
            row1 += 'Ajalta: {billing_period_start_date}-{billing_period_end_date}  '.format(
                billing_period_start_date=self.invoice.billing_period_start_date.strftime('%d.%m.%Y'),
                billing_period_end_date=self.invoice.billing_period_end_date.strftime('%d.%m.%Y'))
        bill_texts.append(row1)

        row2 = 'Päättymispvm: {lease_end_date}  '.format(
            lease_end_date=self.invoice.lease.end_date.strftime('%d.%m.%Y') if self.invoice.lease.end_date else '-')

        if self.invoice.lease.intended_use:
            row2 += 'Käyttötarkoitus: {lease_intended_use}  '.format(
                lease_intended_use=self.invoice.lease.intended_use.name[:25])
        bill_texts.append(row2)

        # It's possible that the rent starts after the invoicing date, so there is no active rent.
        # Rather than trying to guess which rent to use to calculate the yearly cost and index check date,
        # ...just skip the row.
        if rent:
            index_date = '1.1.'
            if rent.cycle == RentCycle.APRIL_TO_MARCH:
                index_date = '1.4.'

            bill_texts.append('Indeksin tark.pvm: {index_date}  Vuosivuokra: {year_rent}  '.format(
                index_date=index_date,
                year_rent='{:.2f}'.format(year_rent.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)).replace('.', ',')))

        bill_texts.append('Vuokrakohde: {real_property_identifier}, {address}  '.format(
            real_property_identifier=real_property_identifier, address=address))

        if self.invoice.notes:
            bill_texts.append(self.invoice.notes)

        return '\n'.join(bill_texts)

    def get_first_tenant(self):
        for invoice_row in self.invoice.rows.all():
            if not invoice_row.tenant:
                continue

            return invoice_row.tenant

    def get_order_party_contact(self):
        tenant = self.get_first_tenant()
        if not tenant or not self.invoice.billing_period_start_date:
            # TODO:
            return self.invoice.recipient

        tenant_tenantcontact = tenant.get_tenant_tenantcontacts(
            self.invoice.billing_period_start_date, self.invoice.billing_period_end_date).first()

        if tenant_tenantcontact:
            return tenant_tenantcontact.contact

        # TODO: If no tenants in rows

    def get_billing_party_contact(self):
        order_party_contact = self.get_order_party_contact()

        if order_party_contact and order_party_contact != self.invoice.recipient:
            return self.invoice.recipient

    def get_po_number(self):
        # Get reference from the tenant that is the same contact
        # as the recipient. Or all references from all of the tenants.
        references = []
        for invoice_row in self.invoice.rows.filter(tenant__isnull=False):
            start_date = self.invoice.billing_period_start_date
            end_date = self.invoice.billing_period_end_date

            # There might be invoices that have no billing_period_start and end_date at all!
            # If this is the case, use the invoicing date to find the proper contacts
            if not start_date and not end_date:
                start_date = end_date = self.invoice.invoicing_date

            tenant_tenantcontact = invoice_row.tenant.get_tenant_tenantcontacts(start_date, end_date).first()
            if (tenant_tenantcontact and tenant_tenantcontact.contact and
                    tenant_tenantcontact.contact == self.invoice.recipient):
                if invoice_row.tenant.reference:
                    return invoice_row.tenant.reference[:35]

            if invoice_row.tenant.reference:
                references.append(invoice_row.tenant.reference)

        if references:
            return ' '.join(references)[:35]

    def set_dates(self):
        billing_date = self.invoice.due_date.replace(day=1)
        self.sales_order.billing_date = billing_date.strftime('%Y%m%d')

        due_date = self.invoice.due_date
        if not is_business_day(due_date):
            due_date = get_next_business_day(due_date)
            self.invoice.adjusted_due_date = due_date
            self.invoice.save()

        value_date = due_date - relativedelta(days=settings.LASKE_DUE_DATE_OFFSET_DAYS)
        self.sales_order.value_date = value_date.strftime('%Y%m%d')

    def set_references(self):
        self.sales_order.reference = str(self.invoice.generate_number())
        self.sales_order.reference_text = self.invoice.lease.get_identifier_string()

    def get_line_items(self):
        line_items = []

        invoice_rows = self.invoice.rows.all()
        for i, invoice_row in enumerate(invoice_rows):
            line_item = LineItem()

            if invoice_row.receivable_type == self.receivable_type_rent:
                line_item.material = self.invoice.lease.type.sap_material_code
                line_item.order_item_number = self.invoice.lease.type.sap_order_item_number
            else:
                line_item.material = invoice_row.receivable_type.sap_material_code
                line_item.order_item_number = invoice_row.receivable_type.sap_order_item_number

            line_item.quantity = '1,00'
            line_item.net_price = '{:.2f}'.format(invoice_row.amount).replace('.', ',')

            line1_strings = ['{}'.format(invoice_row.receivable_type.name)]

            if invoice_row.billing_period_start_date and invoice_row.billing_period_end_date:
                line1_strings.append('{} - {}'.format(
                    invoice_row.billing_period_start_date.strftime('%d.%m.%Y'),
                    invoice_row.billing_period_end_date.strftime('%d.%m.%Y'),
                ))

            line1_strings.append(' ')

            line_item.line_text_l1 = ' '.join(line1_strings)[:70]

            if invoice_row.tenant:
                # NB! As can be seen below, here the billing_period_start_date was used twice originally.
                # I believe it's a mistake, but I'm leaving it here as a reminder in case some weird bugs pop up.
                # tenant_contact = invoice_row.tenant.get_tenant_tenantcontacts(
                #     invoice_row.billing_period_start_date,
                #     invoice_row.billing_period_start_date).first()

                start_date = self.invoice.billing_period_start_date
                end_date = self.invoice.billing_period_end_date

                # There might be invoices that have no billing_period_start and end_date at all!
                # If this is the case, use the invoicing date to find the proper contacts
                if not start_date and not end_date:
                    start_date = end_date = self.invoice.invoicing_date

                tenant_contact = invoice_row.tenant.get_tenant_tenantcontacts(start_date, end_date).first()

                if tenant_contact and tenant_contact.contact:
                    line_item.line_text_l2 = '{}  '.format(tenant_contact.contact.get_name()[:68])

            if i == len(invoice_rows) - 1:
                line_item.line_text_l4 = '   Maksun suorittaminen: Maksu on suoritettava viimeistään eräpäivänä.'
                line_item.line_text_l5 = ' Eräpäivän jälkeen peritään korkolain mukainen viivästyskorko ja'
                line_item.line_text_l6 = ' mahdollisista perimistoimenpiteistä perimispalkkio.'

            line_items.append(line_item)

        return line_items

    def get_order_type(self):
        if self.invoice.type == InvoiceType.CHARGE:
            return 'ZTY1'
        elif self.invoice.type == InvoiceType.CREDIT_NOTE:
            return 'ZHY1'

    def get_original_order(self):
        if self.invoice.type == InvoiceType.CREDIT_NOTE:
            return str(self.invoice.credited_invoice.number)

    def get_sales_office(self):
        if self.invoice.lease.lessor and self.invoice.lease.lessor.sap_sales_office:
            return self.invoice.lease.lessor.sap_sales_office

        # TODO: Remove
        return '2826'

    def set_values(self):
        self.sales_order.set_bill_texts_from_string(self.get_bill_text())

        order_party_contact = self.get_order_party_contact()
        order_party = OrderParty()
        order_party.from_contact(order_party_contact)
        self.sales_order.order_party = order_party

        billing_party_contact = self.get_billing_party_contact()
        if billing_party_contact:
            billing_party1 = BillingParty1()
            billing_party1.from_contact(billing_party_contact)
            self.sales_order.billing_party1 = billing_party1

        self.sales_order.sales_office = self.get_sales_office()
        self.sales_order.po_number = self.get_po_number()
        self.sales_order.order_type = self.get_order_type()
        self.sales_order.original_order = self.get_original_order()

        self.set_dates()
        self.set_references()

        line_items = self.get_line_items()
        self.sales_order.line_items = line_items
