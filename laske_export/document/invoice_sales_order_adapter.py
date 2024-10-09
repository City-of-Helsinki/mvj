import logging
import textwrap
from decimal import ROUND_HALF_UP, Decimal

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import QuerySet

from leasing.enums import (
    InvoiceType,
    RentCycle,
    SapSalesOfficeNumber,
    SapSalesOrgNumber,
    ServiceUnitId,
)
from leasing.models import Contact, Invoice, InvoiceRow, ServiceUnit, Tenant
from leasing.models.utils import get_next_business_day, is_business_day

from .sales_order import BillingParty1, LineItem, OrderParty, SalesOrder

logger = logging.getLogger(__name__)


class InvoiceSalesOrderAdapter:
    """Adapter for invoice sales orders to use in Laske exports.

    Currently contains the MaKe service unit logic, which is the default logic
    until a service unit requests customizations to their exports, like AKV did.

    For service-unit-aware instantiation of class objects, please use the
    factory function invoice_sales_order_adapter_factory
    """

    def __init__(
        self,
        invoice: Invoice,
        sales_order: SalesOrder,
        service_unit: ServiceUnit,
        fill_priority_and_info=True,
    ):
        self.invoice = invoice
        self.sales_order = sales_order
        self.service_unit = service_unit
        self.fill_priority_and_info = fill_priority_and_info

    def get_bill_text(
        self,
    ) -> str:
        if (
            self.invoice.billing_period_start_date
            and self.invoice.billing_period_end_date
        ):
            invoice_year = self.invoice.billing_period_start_date.year

            # TODO: Which rent? Always the first?
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

    def get_first_tenant(self) -> Tenant | None:
        for invoice_row in self.invoice.rows.all():
            if not invoice_row.tenant:
                continue

            return invoice_row.tenant

    def get_contact_to_bill(self) -> Contact:
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

    def get_po_number(self) -> str | None:
        # Simply return the first reference ("viite") we come across
        for invoice_row in self.invoice.rows.filter(tenant__isnull=False):
            if invoice_row.tenant.reference:
                return invoice_row.tenant.reference[:35]

    def set_dates(self) -> None:
        billing_date = self.invoice.due_date.replace(day=1)
        self.sales_order.billing_date = billing_date.strftime("%Y%m%d")

        due_date = self.invoice.due_date
        if not is_business_day(due_date):
            due_date = get_next_business_day(due_date)
            self.invoice.adjusted_due_date = due_date
            self.invoice.save()

        value_date = due_date - relativedelta(days=settings.LASKE_DUE_DATE_OFFSET_DAYS)
        self.sales_order.value_date = value_date.strftime("%Y%m%d")

    def set_references(self) -> None:
        self.sales_order.reference = str(self.invoice.generate_number())
        self.sales_order.reference_text = self.invoice.lease.get_identifier_string()

    def get_line_items(self) -> list[LineItem]:
        line_items = []

        invoice_rows: QuerySet[InvoiceRow] = self.invoice.rows.all()
        for i, invoice_row in enumerate(invoice_rows):
            line_item = LineItem()

            self.set_line_item_common_values(line_item, invoice_row)

            # Create and set the LineTextL<number> elements
            linetext = self.get_line_text(invoice_row)
            is_last_invoicerow = i == len(invoice_rows) - 1
            self.set_linetexts_from_string(line_item, linetext, is_last_invoicerow)

            line_items.append(line_item)

        return line_items

    def set_line_item_common_values(
        self, line_item: LineItem, invoice_row: InvoiceRow
    ) -> None:
        line_item.quantity = "1,00"
        line_item.net_price = "{:.2f}".format(invoice_row.amount).replace(".", ",")

        # Service unit default receivable types for rent and collateral might be
        # null, but we need to check if SAP codes exist in them.
        service_unit_default_rent_material_code = getattr(
            self.service_unit.default_receivable_type_rent,
            "sap_material_code",
            None,
        )
        service_unit_default_rent_order_item_number = getattr(
            self.service_unit.default_receivable_type_rent,
            "sap_order_item_number",
            None,
        )
        if (
            invoice_row.receivable_type
            == self.service_unit.default_receivable_type_rent
            and not service_unit_default_rent_material_code
            and not service_unit_default_rent_order_item_number
        ):
            # If the receivable type is "rent" ("Maanvuokraus"), it probably doesn't have
            # its own SAP codes, so we look up the codes from LeaseType
            line_item.material = self.invoice.lease.type.sap_material_code
            line_item.order_item_number = self.invoice.lease.type.sap_order_item_number

        # ...but in other cases the SAP codes are found in InvoiceRow's ReceivableType.
        elif (
            invoice_row.receivable_type
            == self.service_unit.default_receivable_type_collateral
        ):
            # In case of collateral ("Rahavakuus") receivable type, populate the
            # ProfitCenter element instead of OrderItemNumber element
            line_item.material = invoice_row.receivable_type.sap_material_code
            line_item.profit_center = invoice_row.receivable_type.sap_order_item_number
        else:
            # Otherwise, use SAP codes from the InvoiceRow's receivable type
            line_item.material = invoice_row.receivable_type.sap_material_code
            line_item.order_item_number = (
                invoice_row.receivable_type.sap_order_item_number
            )

        # Sometimes lease has an internal order.
        # In this case, check other relevant business conditions and use it as
        # the order item number.
        if self.invoice.lease.internal_order and (
            self.invoice.lease.service_unit.laske_sales_org
            == SapSalesOrgNumber.KUVA.value
            or invoice_row.receivable_type
            == self.service_unit.default_receivable_type_rent
        ):
            line_item.order_item_number = self.invoice.lease.internal_order

    def get_line_text(self, invoice_row: InvoiceRow) -> str:
        """Generates contents of the LineTextL<number> elements in LineItem."""
        receivable_type_text = (
            invoice_row.receivable_type.name if invoice_row.receivable_type else ""
        )
        # Billing period text
        if (
            invoice_row.billing_period_start_date
            and invoice_row.billing_period_end_date
        ):
            billing_period_text = f"{invoice_row.billing_period_start_date.strftime('%d.%m.%Y')} - \
                {invoice_row.billing_period_end_date.strftime('%d.%m.%Y')}"
        else:
            billing_period_text = ""

        # Contact name text
        if invoice_row.tenant:
            start_date = self.invoice.billing_period_start_date
            end_date = self.invoice.billing_period_end_date

            # There might be invoices that have no billing_period_start and end_date at all.
            # If this is the case, use the invoicing date to find the proper contacts
            if not start_date and not end_date:
                start_date = end_date = self.invoice.invoicing_date

            first_tenantcontact = invoice_row.tenant.get_tenant_tenantcontacts(
                start_date, end_date
            ).first()

            if first_tenantcontact and first_tenantcontact.contact:
                contact_name_text = first_tenantcontact.contact.get_name()
            else:
                contact_name_text = ""
        else:
            contact_name_text = ""

        # Formulate the full linetext in the format as before
        return f"{receivable_type_text} {billing_period_text}  \n{contact_name_text}  "

    def set_linetexts_from_string(
        self, line_item: LineItem, text: str, is_last_invoicerow: bool = False
    ) -> None:
        """Set the LineTextL<number> XML elements in the LineItem.

        Linetext will be wrapped to a maximum line length, and number of lines.
        If there is not enough text to fill all the lines, adds empty string to
        the remaining lines.
        """
        number_of_linetext_lines = 6
        line_max_length = 70

        if is_last_invoicerow:
            # In the last invoicerow, Make/tontit has some lines about
            # payment practices at the end, separated from invoicerow linetext
            # with an empty line...
            last_rows_text = (
                "\n"
                "   Maksun suorittaminen: Maksu on suoritettava viimeistään eräpäivänä."
                " Eräpäivän jälkeen peritään korkolain mukainen viivästyskorko ja"
                " mahdollisista perimistoimenpiteistä perimispalkkio."
            )
            last_rows_lines = textwrap.wrap(
                last_rows_text,
                width=line_max_length,
                drop_whitespace=False,
            )
            # ... which means that the last invoicerow gets less space for its linetext
            first_rows_lines = textwrap.wrap(
                text,
                width=line_max_length,
                max_lines=number_of_linetext_lines - len(last_rows_lines),
                drop_whitespace=False,
            )
            text_lines = first_rows_lines + last_rows_lines
        else:
            # For invoicerows other than the last one, we can use all the
            # available lines for the linetext
            text_lines = textwrap.wrap(
                text,
                width=line_max_length,
                max_lines=number_of_linetext_lines,
                drop_whitespace=False,
            )

        # Set the linetexts to the lineitem
        for i in range(0, number_of_linetext_lines):
            line = text_lines[i] if i < len(text_lines) else ""
            setattr(line_item, f"line_text_l{i+1}", line)

    def get_order_type(self) -> str | None:
        if self.invoice.type == InvoiceType.CHARGE:
            return "ZTY1"
        elif self.invoice.type == InvoiceType.CREDIT_NOTE:
            return "ZHY1"

    def get_original_order(self) -> str | None:
        if self.invoice.type == InvoiceType.CREDIT_NOTE:
            return str(self.invoice.credited_invoice.number)

    def get_sales_office(self) -> str:
        if self.invoice.lease.lessor and self.invoice.lease.lessor.sap_sales_office:
            return self.invoice.lease.lessor.sap_sales_office

        # TODO: What should be the default value when SAP sales office is not found?
        #       Make, or something else? Maybe return empty string instead?
        return SapSalesOfficeNumber.MAKE.value

    def set_values(self) -> None:
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

        self.sales_order.line_items = self.get_line_items()


class AkvInvoiceSalesOrderAdapter(InvoiceSalesOrderAdapter):
    """Adapter for service unit Alueiden kehittäminen ja valvonta.

    For service-unit-aware instantiation of class objects, please use the
    factory function invoice_sales_order_adapter_factory
    """

    AKV_DATE_FORMAT = "%d.%m.%Y"

    def get_bill_text(self) -> str:
        """Create billtext for AKV service unit.

        AKV requested that "Hki otsikko ulkoinen" is left empty in their SAP.
        "Hki otsikko ulkoinen" corresponds to XML elements BillTextL<number> in
        the MVJ export.
        """
        number_of_billtext_lines = 6
        return "\n" * number_of_billtext_lines

    def get_line_items(self) -> list[LineItem]:
        """Create LineItems for AKV service unit."""
        line_items: list[LineItem] = []
        invoice_rows = self.invoice.rows.all()

        for invoice_row in invoice_rows:
            line_item = LineItem()
            self.set_line_item_common_values(line_item, invoice_row)

            linetext = self.get_line_text(invoice_row)
            self.set_linetexts_from_string(line_item, linetext)

            line_items.append(line_item)

        return line_items

    def get_line_text(self, invoice_row: InvoiceRow) -> str:
        """Generates contents of the LineTextL<number> elements in LineItem for
        AKV service unit."""
        intended_use_text = (
            invoice_row.intended_use.name
            if invoice_row.intended_use
            else "<käyttötarkoitus>"
        )

        # TODO Which area to use when multiple areas in lease?
        #      Selecting the first area has been the logic so far in Make exports.
        first_lease_area = self.invoice.lease.lease_areas.first()
        if not first_lease_area:
            logger.error(f"No LeaseAreas found for lease ID {self.invoice.lease.id}")

        area_m2_text = first_lease_area.area if first_lease_area else "<pinta-ala>"

        first_lease_area_address = first_lease_area.addresses.order_by(
            "-is_primary"
        ).first()  # Note: will be non-primary if no primary addresses exist
        address_text = (
            first_lease_area_address.address if first_lease_area_address else "<osoite>"
        )
        postal_code_text = (
            first_lease_area_address.postal_code
            if first_lease_area_address
            else "<postinumero>"
        )

        district = self.invoice.lease.district
        district_name_text = district.name if district else "<kaupunginosa>"
        district_identifier_text = (
            district.identifier if district else "<kaupunginosan tunniste>"
        )

        decision = first_lease_area.archived_decision
        decision_reference_number_text = (
            decision.reference_number if decision else "<diaarinumero>"
        )
        decision_date_text = (
            decision.decision_date.strftime("%d.%m.%Y")
            if decision
            else "<päätöksen pvm>"
        )
        decision_section_text = decision.section if decision else "<pykälä>"

        billing_period_start_date_text = (
            (invoice_row.billing_period_start_date.strftime(self.AKV_DATE_FORMAT))
            if invoice_row.billing_period_start_date
            else "<laskutuskauden alkupvm>"
        )
        billing_period_end_date_text = (
            invoice_row.billing_period_end_date.strftime(self.AKV_DATE_FORMAT)
            if invoice_row.billing_period_end_date
            else "<laskutuskauden loppupvm>"
        )

        # Formulate the full text contents without linebreaks
        return (
            f"Kohde: {intended_use_text}, noin {area_m2_text} m², "
            f"{district_name_text} ({district_identifier_text}), "
            f"{address_text}, {postal_code_text}. "
            f"Päätös: {decision_reference_number_text}, {decision_date_text} § {decision_section_text}, "
            f"{billing_period_start_date_text}-{billing_period_end_date_text}"
        )

    def set_linetexts_from_string(
        self, line_item: LineItem, text: str, is_last_invoicerow: bool = False
    ) -> None:
        """Set the LineTextL<number> XML elements in the LineItem for AKV
        service unit.

        AKV doesn't need the invoicing instructions that are added to the last
        invoicerow in Make/Tontit invoices.

        Linetext will be wrapped to a maximum line length, and number of lines.
        If there is not enough text to fill all the lines, adds empty string to
        the remaining lines.
        """
        # This variable is unused in this child class, but I wanted to avoid a more
        # complicated class structure at this stage when we don't know the KUVA logic yet
        del is_last_invoicerow

        number_of_linetext_lines = 6
        line_max_length = 70

        text_lines = textwrap.wrap(
            text,
            width=line_max_length,
            max_lines=number_of_linetext_lines,
            drop_whitespace=False,
        )
        for i in range(0, number_of_linetext_lines):
            line = text_lines[i] if i < len(text_lines) else ""
            setattr(line_item, f"line_text_l{i+1}", line)


def invoice_sales_order_adapter_factory(
    invoice: Invoice,
    sales_order: SalesOrder,
    service_unit: ServiceUnit,
    fill_priority_and_info: bool = True,
) -> InvoiceSalesOrderAdapter | AkvInvoiceSalesOrderAdapter:
    """Instantiates an invoice sales order adapter based on invoice's service unit.

    AKV SAP export requires billtext and linetext to be different from the
    previously used Make/Tontit logic.
    """
    if invoice.service_unit.id == ServiceUnitId.AKV:
        adapter = AkvInvoiceSalesOrderAdapter
    else:
        adapter = InvoiceSalesOrderAdapter

    return adapter(
        invoice=invoice,
        sales_order=sales_order,
        service_unit=service_unit,
        fill_priority_and_info=fill_priority_and_info,
    )
