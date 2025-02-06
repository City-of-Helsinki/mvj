class FileScanPendingError(Exception):
    """File has not yet been scanned for viruses."""

    pass


class FileUnsafeError(Exception):
    """File has been found unsafe by virus scan."""

    pass


class FileScanError(Exception):
    """Virus scan failed for this file."""
