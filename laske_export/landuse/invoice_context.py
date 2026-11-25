import datetime
import logging
import textwrap
from dataclasses import dataclass, field, fields
from decimal import Decimal
from typing import TYPE_CHECKING, Any, ClassVar, Iterable, cast

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.template.loader import render_to_string

from landuse.models.invoice import InvoiceType
from landuse.models.party import PartyType

if TYPE_CHECKING:
    from landuse.models.invoice import Invoice, InvoiceRecipientSnapshot

logger = logging.getLogger(__name__)
LANDUSE_PAYMENT_REFERENCE_PREFIX = "281"


def _wrap_sap_text(text: str, *, line_length: int, line_count: int) -> tuple[str, ...]:
    """
    Wraps by word boundary if possible.
    """

    lines = textwrap.wrap(text, width=line_length, drop_whitespace=False)
    if len(lines) > line_count:
        logger.warning(
            "SAP text exceeds the %d-line limit; omitting %d wrapped lines.",
            line_count,
            len(lines) - line_count,
        )
    lines = lines[:line_count]
    lines.extend([""] * (line_count - len(lines)))
    return tuple(lines)


class SapFieldValidation:
    MAX_LENGTHS: ClassVar[dict[str, int]] = {}

    def __post_init__(self) -> None:
        for context_field in fields(cast(Any, self)):
            max_length = self.MAX_LENGTHS.get(context_field.name)
            if not hasattr(self, context_field.name):
                continue
            value = getattr(self, context_field.name)
            if max_length is None or len(value) <= max_length:
                continue

            object.__setattr__(self, context_field.name, value[:max_length])
            logger.warning(
                "Truncated SAP field %s.%s from %d to %d characters; "
                "%d characters discarded.",
                type(self).__name__,
                context_field.name,
                len(value),
                max_length,
                len(value) - max_length,
            )


@dataclass(frozen=True)
class SapPartyContext(SapFieldValidation):
    NAME_FIELD_COUNT = 4
    ADDRESS_FIELD_COUNT = 2
    MAX_LENGTHS: ClassVar[dict[str, int]] = {
        "sap_customer_id": 10,
        "customer_id": 11,
        "customer_yid": 9,
        "customer_ovt": 18,
        "name": 35 * NAME_FIELD_COUNT,
        "address": 35 * ADDRESS_FIELD_COUNT,
        "city": 35,
        "postal_code": 9,
    }

    sap_customer_id: str
    customer_id: str
    customer_yid: str
    customer_ovt: str
    name: str
    name_lines: tuple[str, ...] = field(init=False, default=())
    address: str
    address_lines: tuple[str, ...] = field(init=False, default=())
    city: str
    postal_code: str

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(
            self,
            "name_lines",
            _wrap_sap_text(self.name, line_length=35, line_count=self.NAME_FIELD_COUNT),
        )
        object.__setattr__(
            self,
            "address_lines",
            _wrap_sap_text(
                self.address, line_length=35, line_count=self.ADDRESS_FIELD_COUNT
            ),
        )


@dataclass(frozen=True)
class SapLineItemContext(SapFieldValidation):
    LINETEXT_COUNT = 6
    MAX_LENGTHS: ClassVar[dict[str, int]] = {
        "quantity": 13,
        "net_price": 14,
        "linetext": 70 * LINETEXT_COUNT,
    }

    quantity: str
    net_price: str
    linetext: str
    linetext_lines: tuple[str, ...] = field(init=False, default=())

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(
            self,
            "linetext_lines",
            _wrap_sap_text(
                self.linetext, line_length=70, line_count=self.LINETEXT_COUNT
            ),
        )


@dataclass(frozen=True)
class SapSalesOrderContext(SapFieldValidation):
    MAX_LENGTHS: ClassVar[dict[str, int]] = {
        "sender_id": 5,
        "reference": 10,
        "reference_text": 20,
        "payment_reference": 30,
        "order_type": 4,
        "sales_org": 4,
        "distribution_channel": 2,
        "division": 2,
        "sales_office": 4,
        "po_number": 35,
        "pmntterm": 4,
        "billing_date": 8,
        "value_date": 8,
    }

    sender_id: str
    reference: str
    reference_text: str
    payment_reference: str  # The reference that customer uses when paying.
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
    customer_id = (
        recipient.national_identification_number
        if recipient.party_type == PartyType.PERSON.value
        else ""
    )
    customer_yid = (
        recipient.business_id if recipient.party_type == PartyType.COMPANY.value else ""
    )
    return SapPartyContext(
        sap_customer_id=recipient.sap_customer_number,
        customer_id=customer_id,
        customer_yid=customer_yid,
        customer_ovt=recipient.ovt_code,
        name=recipient.name,
        address=recipient.street_address,
        city=recipient.city,
        postal_code=recipient.postal_code,
    )


def _format_amount(amount: Decimal) -> str:
    return f"{amount:.2f}".replace(".", ",")


def _format_date_to_str_YYYYMMDD(date: datetime.date | None) -> str:
    if not date:
        return ""
    return date.strftime("%Y%m%d")


def _sales_order_context(invoice: "Invoice") -> SapSalesOrderContext:
    recipient = invoice.recipient_snapshot
    party = _party_context(recipient)
    return SapSalesOrderContext(
        sender_id=_sap_value("sender_id"),
        reference=str(invoice.invoice_identifier),
        reference_text=invoice.agreement.identifier,
        payment_reference=get_payment_reference(invoice.invoice_identifier),
        order_type=get_order_type(invoice.invoice_type),
        sales_org=_sap_value("sales_org"),
        distribution_channel=_sap_value("distribution_channel"),
        division=_sap_value("division"),
        sales_office=_sap_value("sales_office"),
        po_number=recipient.customer_reference,
        pmntterm=_sap_value("pmntterm"),
        billing_date=get_billing_date(invoice.due_date),
        value_date=get_value_date(invoice.due_date),
        order_party=party,
        billing_party1=party,
        line_items=tuple(
            SapLineItemContext(
                quantity="1,00",
                net_price=_format_amount(item.amount),
                linetext=item.description,
            )
            for item in invoice.items.all()
        ),
    )


def get_billing_date(due_date: datetime.date) -> str:
    """Logic copied from leasing export."""

    billing_date = due_date.replace(day=1)
    return _format_date_to_str_YYYYMMDD(billing_date)


def get_value_date(due_date: datetime.date) -> str:
    """
    Follows old leasing logic in which value date is derived
    from due date by offsetting a certain number of days.
    """

    value_date = due_date - relativedelta(
        days=getattr(settings, "LASKE_DUE_DATE_OFFSET_DAYS")
    )
    return _format_date_to_str_YYYYMMDD(value_date)


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
    context = _sales_order_context(invoice)
    sales_order = render_to_string(
        "landuse/sales_order.xml", {"order": context}
    ).strip()
    if include_container:
        return render_sales_order_container([sales_order])
    return sales_order
