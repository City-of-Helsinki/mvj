import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, TypeAlias, TypedDict, Union

from leasing.calculation.explanation import Explanation
from leasing.enums import InvoiceState, InvoiceType

if TYPE_CHECKING:
    # Avoid circular imports
    from leasing.calculation.result import CalculationResult
    from leasing.models.contact import Contact  # noqa: F401
    from leasing.models.invoice import ReceivableType
    from leasing.models.lease import Lease
    from leasing.models.rent import (
        ContractRent,
        FixedInitialYearRent,
        RentAdjustment,
        RentIntendedUse,
    )
    from leasing.models.service_unit import ServiceUnit
    from leasing.models.tenant import Tenant  # noqa: F401

DueDate: TypeAlias = datetime.date


class PayableRent(TypedDict):
    due_date: DueDate
    calculation_result: "CalculationResult"
    last_billing_period: bool


BillingPeriod: TypeAlias = tuple[datetime.date, datetime.date]
PayableRentsInPeriods = dict[BillingPeriod, PayableRent]

Periods: TypeAlias = list[tuple[datetime.date, datetime.date]]
TenantPeriods: TypeAlias = dict["Tenant", Periods]
TenantShares: TypeAlias = dict["Contact", TenantPeriods]

InvoiceNoteNotes: TypeAlias = list[str]


class CalculationAmountRows(TypedDict):
    tenant: "Tenant"
    receivable_type: "ReceivableType"
    intended_use: "RentIntendedUse"
    billing_period_start_date: BillingPeriod
    billing_period_end_date: BillingPeriod
    amount: Decimal


CalculationAmountsByContact = dict["Contact", list[CalculationAmountRows]]

CalculationAmountItem: TypeAlias = Union[
    "FixedInitialYearRent", "ContractRent", "RentAdjustment"
]

CalculationAmountsSum: TypeAlias = Decimal


class InvoiceDatum(TypedDict):
    type: InvoiceType
    lease: "Lease"
    recipient: "Contact"
    due_date: DueDate
    billing_period_start_date: BillingPeriod
    billing_period_end_date: BillingPeriod
    total_amount: CalculationAmountsSum
    billed_amount: CalculationAmountsSum
    rows: CalculationAmountRows
    explanations: list[Explanation]
    calculation_result: "CalculationResult"
    state: InvoiceState
    notes: InvoiceNoteNotes
    service_unit: "ServiceUnit"
