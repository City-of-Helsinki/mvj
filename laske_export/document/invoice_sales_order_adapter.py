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
        if self.invoice.billing_period_start_date:
            invoice_year = self.invoice.billing_period_start_date.year
        else:
            invoice_year = self.invoice.invoicing_date.year

        year_rent = self.invoice.lease.get_rent_amount_for_year(invoice_year)

        real_property_identifier = ''
        address = ''

        first_lease_area = self.invoice.lease.lease_areas.first()
        if first_lease_area:
            real_property_identifier = first_lease_area.identifier
            lease_area_address = first_lease_area.addresses.first()
            if lease_area_address:
                address = lease_area_address.address

        index_date = '1.1.'
        # TODO: Which rent
        rent = self.invoice.lease.get_active_rents_on_period(
            self.invoice.invoicing_date, self.invoice.invoicing_date).first()
        if rent.cycle == RentCycle.APRIL_TO_MARCH:
            index_date = '1.4.'

        bill_texts = []
        bill_texts.append('Vuokraustunnus: {lease_identifier}'.format(
            lease_identifier=self.invoice.lease.get_identifier_string()))
        if self.invoice.billing_period_start_date and self.invoice.billing_period_end_date:
            bill_texts.append('Vuokra ajalta: {billing_period_start_date}-{billing_period_end_date}'.format(
                billing_period_start_date=self.invoice.billing_period_start_date.strftime('%d.%m.%Y'),
                billing_period_end_date=self.invoice.billing_period_end_date.strftime('%d.%m.%Y')))
        bill_texts.append('Sopimuksen päättymispvm: {lease_end_date}'.format(
            lease_end_date=self.invoice.lease.end_date.strftime('%d.%m.%Y') if self.invoice.lease.end_date else '-'))
        if self.invoice.lease.intended_use:
            bill_texts.append('Käyttötarkoitus: {lease_intended_use}'.format(
                lease_intended_use=str(self.invoice.lease.intended_use)))
        bill_texts.append('Indeksin tark.pvm: {index_date}  Vuosivuokra: {year_rent}'.format(
            index_date=index_date,
            year_rent='{:.2f}'.format(year_rent.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)).replace('.', ',')))
        bill_texts.append('Kiinteistötunnus: {real_property_identifier}'.format(
            real_property_identifier=real_property_identifier))
        bill_texts.append('Vuokrakohteen osoite: {address}'.format(address=address))

        return '\n  '.join(bill_texts)

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
        tenant = self.get_first_tenant()
        if tenant and tenant.reference:
            return tenant.reference

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
        for invoice_row in self.invoice.rows.all():
            line_item = LineItem()

            if invoice_row.receivable_type == self.receivable_type_rent:
                line_item.material = self.invoice.lease.type.sap_material_code
                line_item.order_item_number = self.invoice.lease.type.sap_order_item_number
            else:
                line_item.material = invoice_row.receivable_type.sap_material_code
                line_item.order_item_number = invoice_row.receivable_type.sap_order_item_number

            line_item.quantity = '1,00'
            line_item.net_price = '{:.2f}'.format(invoice_row.amount).replace('.', ',')

            line_items.append(line_item)

        return line_items

    def get_order_type(self):
        if self.invoice.type == InvoiceType.CHARGE:
            return 'ZTY1'
        elif self.invoice.type == InvoiceType.CREDIT_NOTE:
            return 'ZHY1'

    def get_original_order(self):
        if self.invoice.type == InvoiceType.CREDIT_NOTE:
            return self.invoice.credited_invoice.number

    def get_sales_office(self):
        if self.invoice.lease.lessor and self.invoice.lease.lessor.sap_sales_office:
            return self.invoice.lease.lessor.sap_sales_office

        # TODO: Which value to use?
        return None

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
