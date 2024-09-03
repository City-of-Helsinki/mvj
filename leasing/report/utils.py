# From Django docs
def dictfetchall(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


# Gaps in billing periods helpers


def get_lease_period(billing_period_data_row, today):
    """
    Get the period of the lease with active rents to be compared with the billing periods of the lease's invoices.
    """
    start_date = billing_period_data_row["start_date"]
    if (
        not billing_period_data_row["end_date"]
        or billing_period_data_row["end_date"] > today
    ):
        end_date = today
    else:
        end_date = billing_period_data_row["end_date"]

    return start_date, end_date


def calculate_invoice_billing_period_days(start_date, end_date, today):
    """
    Calculate the billing period days for the invoice.
    Returns None if there are missing dates.
    Excludes invoices and parts of the billing periods that are in the future.
    """
    if start_date is None or end_date is None:
        return None
    if start_date > today:
        return 0
    current_end_date = today
    if end_date < current_end_date:
        current_end_date = end_date
    return (current_end_date - start_date).days + 1
