import datetime
from decimal import Decimal
from typing import TypedDict

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
