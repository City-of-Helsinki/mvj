from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings
from django.template.loader import render_to_string


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
    material_description: str
    quantity: str
    net_price: str
    line_text_l1: str


@dataclass(frozen=True)
class SapSalesOrderContext:
    sender_id: str
    reference: str
    contract_number: str
    order_type: str
    sales_org: str
    distribution_channel: str
    division: str
    sales_office: str
    po_number: str
    reference_text: str
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


def _party_context(recipient) -> SapPartyContext:
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


def render_invoice_xml(invoice) -> str:
    """Render the current invoice as an in-memory SAP sales-order document."""
    recipient = invoice.recipient_snapshot
    party = _party_context(recipient)
    due_date = invoice.due_date.strftime("%Y%m%d") if invoice.due_date else ""
    context = SapSalesOrderContext(
        sender_id=_sap_value("sender_id"),
        reference=invoice.invoice_identifier,
        contract_number=invoice.agreement.identifier,
        order_type=_sap_value("order_type") or "ZTY1",
        sales_org=_sap_value("sales_org"),
        distribution_channel=_sap_value("distribution_channel"),
        division=_sap_value("division"),
        sales_office=_sap_value("sales_office"),
        po_number=recipient.customer_reference,
        reference_text=invoice.agreement.identifier,
        pmntterm=_sap_value("pmntterm"),
        billing_date=due_date,
        value_date=due_date,
        order_party=party,
        billing_party1=party,
        line_items=tuple(
            SapLineItemContext(
                material_description=item.get_item_type_display(),
                quantity="1,00",
                net_price=_format_amount(item.amount),
                line_text_l1=item.description,
            )
            for item in invoice.items.all()
        ),
    )
    return render_to_string("landuse/invoice.xml", {"order": context}).strip()
