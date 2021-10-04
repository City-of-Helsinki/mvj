from django.utils.translation import pgettext_lazy
from enumfields import Enum


class CreditDecisionStatus(Enum):
    """
    In Finnish: Luottopäätöksen tila
    """

    YES = "yes"
    NO = "no"
    CONSIDERATION = "consideration"

    class Labels:
        YES = pgettext_lazy("Credit decision status", "Yes")
        NO = pgettext_lazy("Credit decision status", "No")
        CONSIDERATION = pgettext_lazy("Credit decision status", "Consideration")
