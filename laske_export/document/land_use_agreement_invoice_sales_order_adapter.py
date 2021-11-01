from dateutil.relativedelta import relativedelta
from django.conf import settings

from leasing.models.utils import get_next_business_day, is_business_day

from .sales_order import BillingParty1, LineItem, OrderParty


class LandUseAgreementInvoiceSalesOrderAdapter:
    def __init__(
        self, invoice=None, sales_order=None,
    ):
        self.invoice = invoice
        self.sales_order = sales_order

    def get_bill_text(self):
        bill_texts = []
        row1 = "Maankäyttösopimuksen tunnus:  {identifier}  ".format(
            identifier=str(self.invoice.land_use_agreement.identifier)
        )
        bill_texts.append(row1)

        return "\n".join(bill_texts)

    def get_order_party_contact(self):
        return self.invoice.recipient

    def get_billing_party_contact(self):
        return self.invoice.recipient

    def set_dates(self):
        billing_date = self.invoice.due_date.replace(day=1)
        self.sales_order.billing_date = billing_date.strftime("%Y%m%d")
        due_date = self.invoice.due_date
        if not is_business_day(due_date):
            due_date = get_next_business_day(due_date)
            self.invoice.adjusted_due_date = due_date
            self.invoice.save()

        value_date = due_date - relativedelta(days=settings.LASKE_DUE_DATE_OFFSET_DAYS)
        self.sales_order.value_date = value_date.strftime("%Y%m%d")

    def set_references(self):
        self.sales_order.reference = str(self.invoice.generate_number())

    def get_line_items(self):
        line_items = []

        line_item = LineItem()

        line_item.quantity = "1,00"
        line_item.net_price = "{:.2f}".format(self.invoice.total_amount).replace(
            ".", ","
        )

        line_item.line_text_l4 = (
            "   Maksun suorittaminen: Maksu on suoritettava viimeistään eräpäivänä."
        )
        line_item.line_text_l5 = (
            " Eräpäivän jälkeen peritään korkolain mukainen viivästyskorko ja"
        )
        line_item.line_text_l6 = " mahdollisista perimistoimenpiteistä perimispalkkio."

        line_items.append(line_item)

        return line_items

    def get_order_type(self):
        return "ZTY1"

    def set_values(self):
        self.sales_order.set_bill_texts_from_string(self.get_bill_text())

        order_party_contact = self.get_order_party_contact()
        order_party = OrderParty()
        order_party.from_contact(order_party_contact)
        self.sales_order.order_party = order_party

        billing_party_contact = self.get_billing_party_contact()
        billing_party1 = BillingParty1()
        billing_party1.from_contact(billing_party_contact)
        self.sales_order.billing_party1 = billing_party1

        self.sales_order.order_type = self.get_order_type()

        self.set_dates()
        self.set_references()

        line_items = self.get_line_items()
        self.sales_order.line_items = line_items
