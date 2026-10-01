import datetime
from decimal import Decimal
from typing import Any, TypedDict

from leasing.models.receivable_type import ReceivableType


class CreateChargeInvoiceRowData(TypedDict):
    amount: Decimal
    receivable_type: ReceivableType


class CreateChargeData(TypedDict):
    due_date: datetime.date
    billing_period_start_date: datetime.date
    billing_period_end_date: datetime.date
    rows: list[CreateChargeInvoiceRowData]
    notes: str


class RelatedLeaseEdge(TypedDict):
    predecessor: int
    successor: int
    related_lease_id: int


class RelatedLeases(TypedDict):
    current_lease_id: int
    leases: dict[str, Any]
    edges: list[RelatedLeaseEdge]
