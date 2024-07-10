def get_receivable_type_rent(exporter, invoice) -> int | None:
    """
    Get receivable type to determine whether to include internal order
    in the export.
    """
    if exporter.service_unit.default_receivable_type_rent:
        return exporter.service_unit.default_receivable_type_rent

    if exporter.service_unit.name.includes("KuVa"):
        if invoice.lease.is_subject_to_vat is True:
            # TODO: What is the id of the receivable type for KuVa WITH VAT that needs the internal order number?
            # Logic for getting the receivable type id for KuVa WITH VAT
            return 123

        # TODO: What is the id of the receivable type for KuVa WITHOUT VAT that needs the internal order number?
        # Logic for getting the receivable type id for KuVa WITHOUT VAT
        return 456

    return None
