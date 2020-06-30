from django.utils.translation import pgettext_lazy
from enumfields import Enum


class LaskeExportLogInvoiceStatus(Enum):
    """
    In Finnish: Laske viennin-lokin laskun tila
    """

    SENT = "sent"
    FAILED = "failed"

    class Labels:
        SENT = pgettext_lazy("Laske export log invoice status", "Sent")
        FAILED = pgettext_lazy("Laske export log invoice status", "Failed")
