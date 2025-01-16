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


class FileScanStatusContentType(str, Enum):
    """
    In Finnish: Tiedoston virusskannauksen sisältötyyppi
    """

    FORMS_ATTACHMENT = "forms_attachment"
    INFILL_DEVELOPMENT_COMPENSATION_ATTACHMENT = (
        "leasing_infilldevelopmentcompensationattachment"
    )
    INSPECTION_ATTACHMENT = "leasing_inspectionattachment"
    LAND_USE_AGREEMENT_ATTACHMENT = "leasing_landuseagreementattachment"
    LEASE_AREA_ATTACHMENT = "leasing_leaseareaattachment"
    AREA_SEARCH_ATTACHMENT = "plotsearch_areasearchattachment"

    @classmethod
    def choices(cls):
        return [(field.value, field.name) for field in cls]

    @classmethod
    def values(cls):
        return [field.value for field in cls]
