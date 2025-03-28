import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, TypeAlias, TypedDict, Union

from leasing.calculation.explanation import Explanation
from leasing.enums import InvoiceState, InvoiceType
from leasing.models.receivable_type import ReceivableType

if TYPE_CHECKING:
    # Avoid circular imports
    from leasing.calculation.result import CalculationResult
    from leasing.models.contact import Contact  # noqa: F401
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
    override_receivable_type: ReceivableType | None


BillingPeriod: TypeAlias = tuple[datetime.date, datetime.date]
PayableRentsInPeriods = dict[BillingPeriod, PayableRent]

Periods: TypeAlias = list[tuple[datetime.date, datetime.date]]
TenantPeriods: TypeAlias = dict["Tenant", Periods]
TenantShares: TypeAlias = dict["Contact", TenantPeriods]

InvoiceNoteNotes: TypeAlias = list[str]


class CalculationAmountRow(TypedDict):
    """Roughly analogous to InvoiceRow"""

    tenant: "Tenant"
    receivable_type: "ReceivableType"
    intended_use: "RentIntendedUse"
    billing_period_start_date: BillingPeriod
    billing_period_end_date: BillingPeriod
    amount: Decimal


CalculationAmountsByContact = dict["Contact", list[CalculationAmountRow]]

CalculationAmountItem: TypeAlias = Union[
    "FixedInitialYearRent", "ContractRent", "RentAdjustment"
]

CalculationAmountsSum: TypeAlias = Decimal


class InvoiceDatum(TypedDict):
    """Roughly analogous to Invoice"""

    type: InvoiceType
    lease: "Lease"
    recipient: "Contact"
    due_date: DueDate
    billing_period_start_date: BillingPeriod
    billing_period_end_date: BillingPeriod
    total_amount: CalculationAmountsSum
    billed_amount: CalculationAmountsSum
    rows: list[CalculationAmountRow]
    explanations: list[Explanation]
    calculation_result: "CalculationResult"
    state: InvoiceState
    notes: InvoiceNoteNotes
    service_unit: "ServiceUnit"


class InvoiceDatumDict(InvoiceDatum):
    rows: dict[int, CalculationAmountRow]


class ContactsActiveLeases(TypedDict):
    lease_identifier: str
    lease_id: int


class CumulativeTemporarySubvention(TypedDict):
    description: str
    subvention_percent: Decimal
    subvention_amount_euros_per_year: Decimal
