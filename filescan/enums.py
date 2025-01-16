from enum import Enum


class FileScanResult(Enum):
    """
    Result of the malware/virus filescan.

    Pending if not yet scanned, safe if the file was scanned and no threats were
    found, and unsafe if file was scanned and a threat was found.
    """

    PENDING = "Pending"
    SAFE = "Safe"
    UNSAFE = "Unsafe"
    ERROR = "Error"
