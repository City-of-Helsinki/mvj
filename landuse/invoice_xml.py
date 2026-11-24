from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Iterable

from django.conf import settings
from django.template.loader import render_to_string

from landuse.models.invoice import InvoiceType

if TYPE_CHECKING:
    from landuse.models.invoice import Invoice, InvoiceRecipientSnapshot

LANDUSE_PAYMENT_REFERENCE_PREFIX = "281"


@dataclass(frozen=True)
class SapPartyContext:
    sap_customer_id: str
    customer_id: str
    customer_yid: str
    customer_ovt: str
    priority_name1: str
    priority_address1: str
    priority_city: str
    priority_postalcode: str
    info_customer_id: str
    info_customer_yid: str
    info_customer_ovt: str
    info_name1: str
    info_address1: str
    info_city: str
    info_postalcode: str


@dataclass(frozen=True)
class SapLineItemContext:
    quantity: str
    net_price: str
    line_text_l1: str


@dataclass(frozen=True)
class SapSalesOrderContext:
    sender_id: str
    reference: str
    reference_text: str
    payment_reference: str  # The reference that customer uses when paying.
    contract_number: str
    order_type: str
    sales_org: str
    distribution_channel: str
    division: str
    sales_office: str
    po_number: str
    pmntterm: str
    billing_date: str
    value_date: str
    order_party: SapPartyContext
    billing_party1: SapPartyContext
    line_items: tuple[SapLineItemContext, ...]


def _sap_value(name: str) -> str:
    values = getattr(settings, "SAP_LANDUSE_VALUES", None)
    if values is None:
        raise ValueError("SAP_LANDUSE_VALUES is not configured in settings.")

    return str(values.get(name, ""))


def _party_context(recipient: "InvoiceRecipientSnapshot") -> SapPartyContext:
    customer_id = recipient.national_identification_number
    customer_yid = recipient.business_id
    return SapPartyContext(
        sap_customer_id=recipient.sap_customer_number,
        customer_id=customer_id,
        customer_yid=customer_yid,
        customer_ovt=recipient.ovt_code,
        priority_name1=recipient.name,
        priority_address1=recipient.street_address,
        priority_city=recipient.city,
        priority_postalcode=recipient.postal_code,
        info_customer_id=customer_id,
        info_customer_yid=customer_yid,
        info_customer_ovt=recipient.ovt_code,
        info_name1=recipient.name,
        info_address1=recipient.street_address,
        info_city=recipient.city,
        info_postalcode=recipient.postal_code,
    )


def _format_amount(amount: Decimal) -> str:
    return f"{amount:.2f}".replace(".", ",")


def _sales_order_context(invoice: "Invoice") -> SapSalesOrderContext:
    recipient = invoice.recipient_snapshot
    party = _party_context(recipient)
    due_date = invoice.due_date.strftime("%Y%m%d") if invoice.due_date else ""
    return SapSalesOrderContext(
        sender_id=_sap_value("sender_id"),
        reference=str(invoice.invoice_identifier),
        reference_text=invoice.agreement.identifier,
        payment_reference=get_payment_reference(invoice.invoice_identifier),
        contract_number=invoice.agreement.identifier,
        order_type=get_order_type(invoice.invoice_type),
        sales_org=_sap_value("sales_org"),
        distribution_channel=_sap_value("distribution_channel"),
        division=_sap_value("division"),
        sales_office=_sap_value("sales_office"),
        po_number=recipient.customer_reference,
        pmntterm=_sap_value("pmntterm"),
        billing_date=due_date,
        value_date=due_date,
        order_party=party,
        billing_party1=party,
        line_items=tuple(
            SapLineItemContext(
                quantity="1,00",
                net_price=_format_amount(item.amount),
                line_text_l1=item.description,
            )
            for item in invoice.items.all()
        ),
    )


def get_payment_reference(invoice_identifier: int) -> str:
    from laske_export.utils import calculate_payment_reference_checksum

    invoice_number = str(invoice_identifier)
    checksum = calculate_payment_reference_checksum(
        LANDUSE_PAYMENT_REFERENCE_PREFIX + invoice_number
    )
    return f"{LANDUSE_PAYMENT_REFERENCE_PREFIX}{invoice_number}{checksum}"


def get_order_type(invoice_type: InvoiceType | str) -> str:
    if invoice_type == InvoiceType.LAND_USE_COMPENSATION:
        # Comparable to "CHARGE" type in leasing invoices
        return "ZTY1"

    # Credit order type would be "ZHY1", but will be implemented later.
    raise ValueError(f"Unsupported invoice type: {invoice_type}")


def render_invoices_xml(invoices: Iterable["Invoice"]) -> str:
    """Render invoices in a single SAP sales-order container."""
    return render_sales_order_container(
        render_single_invoice_xml(invoice, include_container=False)
        for invoice in invoices
    )


def render_sales_order_container(sales_orders: Iterable[str]) -> str:
    """Wrap already-rendered sales-order XML fragments without rendering them again."""
    return render_to_string(
        "landuse/sales_order_container.xml",
        {"sales_orders": sales_orders},
    ).strip()


def render_single_invoice_xml(
    invoice: "Invoice", *, include_container: bool = True
) -> str:
    """Render the current invoice as an in-memory SAP sales-order document."""
    sales_order = render_to_string(
        "landuse/invoice.xml", {"order": _sales_order_context(invoice)}
    ).strip()
    if include_container:
        return render_sales_order_container([sales_order])
    return sales_order
