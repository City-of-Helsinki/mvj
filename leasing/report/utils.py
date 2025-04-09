from datetime import date
from typing import TypedDict

from django.db.backends.utils import CursorWrapper


class InvoicingGapsRow(TypedDict):
    lease_identifier: str
    lease_id: int
    gap_start_date: date
    gap_end_date: date
    next_start_date: date
    rent_id: int
    rent_start_date: date
    rent_end_date: date
    invoice_id: int
    recipient_name: str


class InvoicingDisabledReportRow(TypedDict):
    section: None
    lease_identifier: str | None
    lease_id: int | None
    start_date: date | None
    end_date: date | None


class InvoicingReviewReportRow(TypedDict):
    section: str | None
    lease_identifier: str | None
    lease_id: int | None
    start_date: date | None
    end_date: date | None
    note: str | None


# From Django docs
def dictfetchall(cursor: CursorWrapper):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_basis_of_rent_type_string(
    choices: list[tuple[str, str]], basis_of_rent_type: str
) -> str:
    """
    Get the string representation of a basis of rent type.
    """
    for choice in choices:
        if choice[0] == basis_of_rent_type:
            return choice[1]
    return basis_of_rent_type
