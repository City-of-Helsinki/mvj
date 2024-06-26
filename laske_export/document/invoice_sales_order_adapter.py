from decimal import ROUND_HALF_UP, Decimal

from dateutil.relativedelta import relativedelta
from django.conf import settings

from leasing.enums import InvoiceType, RentCycle
from leasing.models.utils import get_next_business_day, is_business_day

from .sales_order import BillingParty1, LineItem, OrderParty


class InvoiceSalesOrderAdapter:
    def __init__(
        self,
        invoice=None,
        sales_order=None,
        receivable_type_rent=None,
        receivable_type_collateral=None,
        fill_priority_and_info=True,
    ):
        self.invoice = invoice
        self.sales_order = sales_order
        self.receivable_type_rent = receivable_type_rent
        self.receivable_type_collateral = receivable_type_collateral
        self.fill_priority_and_info = fill_priority_and_info

    def get_bill_text(self):
        if (
            self.invoice.billing_period_start_date
            and self.invoice.billing_period_end_date
        ):
            invoice_year = self.invoice.billing_period_start_date.year

            # TODO: Which rent
            rent = self.invoice.lease.get_active_rents_on_period(
                self.invoice.billing_period_start_date,
                self.invoice.billing_period_end_date,
            ).first()
        else:
            invoice_year = self.invoice.invoicing_date.year

            rent = self.invoice.lease.get_active_rents_on_period(
                self.invoice.invoicing_date, self.invoice.invoicing_date
            ).first()

        rent_calculation = self.invoice.lease.calculate_rent_amount_for_year(
            invoice_year
        )
        year_rent = rent_calculation.get_total_amount()

        real_property_identifier = ""
        address = ""

        first_lease_area = self.invoice.lease.lease_areas.first()
        if first_lease_area:
            real_property_identifier = first_lease_area.identifier
            lease_area_address = first_lease_area.addresses.order_by(
                "-is_primary"
            ).first()

            if lease_area_address:
                address = lease_area_address.address

        bill_texts = []
        row1 = "Vuokraustunnus: {lease_identifier}  ".format(
            lease_identifier=self.invoice.lease.get_identifier_string()
        )

        if (
            self.invoice.billing_period_start_date
            and self.invoice.billing_period_end_date
        ):
            row1 += "Ajalta: {billing_period_start_date}-{billing_period_end_date}  ".format(
                billing_period_start_date=self.invoice.billing_period_start_date.strftime(
                    "%d.%m.%Y"
                ),
                billing_period_end_date=self.invoice.billing_period_end_date.strftime(
                    "%d.%m.%Y"
                ),
            )
        bill_texts.append(row1)

        row2 = "Päättymispvm: {lease_end_date}  ".format(
            lease_end_date=(
                self.invoice.lease.end_date.strftime("%d.%m.%Y")
                if self.invoice.lease.end_date
                else "-"
            )
        )

        if self.invoice.lease.intended_use:
            row2 += "Käyttötarkoitus: {lease_intended_use}  ".format(
                lease_intended_use=self.invoice.lease.intended_use.name[:25]
            )
        bill_texts.append(row2)

        # It's possible that the rent starts after the invoicing date, so there is no active rent.
        # Rather than trying to guess which rent to use to calculate the yearly cost and index check date,
        # ...just skip writing this one description row on the invoice.
        if rent:
            index_date = "1.1."
            if rent.cycle == RentCycle.APRIL_TO_MARCH:
                index_date = "1.4."

            bill_texts.append(
                "Indeksin tark.pvm: {index_date}  Vuosivuokra: {year_rent}  ".format(
                    index_date=index_date,
                    year_rent="{:.2f}".format(
                        year_rent.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
                    ).replace(".", ","),
                )
            )  # noqa: E501

        bill_texts.append(
            "Vuokrakohde: {real_property_identifier}, {address}  ".format(
                real_property_identifier=real_property_identifier, address=address
            )
        )

        if self.invoice.notes:
            bill_texts.append(self.invoice.notes)

        return "\n".join(bill_texts)

    def get_first_tenant(self):
        for invoice_row in self.invoice.rows.all():
            if not invoice_row.tenant:
                continue

            return invoice_row.tenant

    def get_contact_to_bill(self):
        tenant = self.get_first_tenant()
        # We need a tenant and time period to find the BILLING contact
        if not tenant or not self.invoice.billing_period_start_date:
            return self.invoice.recipient

        # This method returns the TENANT contact if there's no BILLING contact
        tenant_billingcontact = tenant.get_billing_tenantcontacts(
            self.invoice.billing_period_start_date, self.invoice.billing_period_end_date
        ).first()

        if not tenant_billingcontact:
            return self.invoice.recipient
        return tenant_billingcontact.contact

    def get_po_number(self):
        # Simply return the first reference ("viite") we come across
        for invoice_row in self.invoice.rows.filter(tenant__isnull=False):
            if invoice_row.tenant.reference:
                return invoice_row.tenant.reference[:35]

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
        self.sales_order.reference_text = self.invoice.lease.get_identifier_string()

    def get_line_items(self):
        line_items = []

        invoice_rows = self.invoice.rows.all()
        for i, invoice_row in enumerate(invoice_rows):
            line_item = LineItem()

            receivable_type = invoice_row.receivable_type
            # If the receivable type is "rent" and doesn't have its own code and
            # item number we look up the SAP codes from the LeaseType
            if (
                receivable_type == self.receivable_type_rent
                and not self.receivable_type_rent.sap_material_code
                and not self.receivable_type_rent.sap_order_item_number
            ):
                line_item.material = self.invoice.lease.type.sap_material_code
                line_item.order_item_number = (
                    self.invoice.lease.type.sap_order_item_number
                )

            # ...but in other cases the SAP codes are found in the ReceivableType object of the invoice row.
            elif receivable_type == self.receivable_type_collateral:
                # In case of a collateral ("Rahavakuus") row, need to populate ProfitCenter element instead
                line_item.profit_center = receivable_type.sap_order_item_number
                line_item.material = receivable_type.sap_material_code
            else:
                line_item.material = receivable_type.sap_material_code
                line_item.order_item_number = receivable_type.sap_order_item_number

            # Finally we'll use internal order from the lease if the receivable type is
            # "rent" and the internal order is set.
            if (
                receivable_type == self.receivable_type_rent
                and self.invoice.lease.internal_order
            ):
                line_item.order_item_number = self.invoice.lease.internal_order

            line_item.quantity = "1,00"
            line_item.net_price = "{:.2f}".format(invoice_row.amount).replace(".", ",")

            line1_strings = ["{}".format(invoice_row.receivable_type.name)]

            if (
                invoice_row.billing_period_start_date
                and invoice_row.billing_period_end_date
            ):
                line1_strings.append(
                    "{} - {}".format(
                        invoice_row.billing_period_start_date.strftime("%d.%m.%Y"),
                        invoice_row.billing_period_end_date.strftime("%d.%m.%Y"),
                    )
                )

            line1_strings.append(" ")

            line_item.line_text_l1 = " ".join(line1_strings)[:70]

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

                tenant_contact = invoice_row.tenant.get_tenant_tenantcontacts(
                    start_date, end_date
                ).first()

                if tenant_contact and tenant_contact.contact:
                    line_item.line_text_l2 = "{}  ".format(
                        tenant_contact.contact.get_name()[:68]
                    )

            if i == len(invoice_rows) - 1:
                line_item.line_text_l4 = "   Maksun suorittaminen: Maksu on suoritettava viimeistään eräpäivänä."
                line_item.line_text_l5 = (
                    " Eräpäivän jälkeen peritään korkolain mukainen viivästyskorko ja"
                )
                line_item.line_text_l6 = (
                    " mahdollisista perimistoimenpiteistä perimispalkkio."
                )

            line_items.append(line_item)

        return line_items

    def get_order_type(self):
        if self.invoice.type == InvoiceType.CHARGE:
            return "ZTY1"
        elif self.invoice.type == InvoiceType.CREDIT_NOTE:
            return "ZHY1"

    def get_original_order(self):
        if self.invoice.type == InvoiceType.CREDIT_NOTE:
            return str(self.invoice.credited_invoice.number)

    def get_sales_office(self):
        if self.invoice.lease.lessor and self.invoice.lease.lessor.sap_sales_office:
            return self.invoice.lease.lessor.sap_sales_office

        # TODO: Remove
        return "2826"

    def set_values(self):
        self.sales_order.set_bill_texts_from_string(self.get_bill_text())

        contact_to_be_billed = self.get_contact_to_bill()

        order_party = OrderParty(fill_priority_and_info=self.fill_priority_and_info)
        order_party.from_contact(contact_to_be_billed)
        self.sales_order.order_party = order_party

        billing_party1 = BillingParty1(
            fill_priority_and_info=self.fill_priority_and_info
        )
        billing_party1.from_contact(contact_to_be_billed)
        self.sales_order.billing_party1 = billing_party1

        self.sales_order.sales_office = self.get_sales_office()
        self.sales_order.po_number = self.get_po_number()
        self.sales_order.order_type = self.get_order_type()
        self.sales_order.original_order = self.get_original_order()

        self.set_dates()
        self.set_references()

        line_items = self.get_line_items()
        self.sales_order.line_items = line_items
