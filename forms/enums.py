from django.utils.translation import pgettext_lazy
from enumfields import Enum


class FormState(str, Enum):
    """
    In Finnish: Tila
    """

    WORK_IN_PROGRESS = "work_in_progress"
    READY = "ready"
    DELETED = "deleted"

    class Labels:
        WORK_IN_PROGRESS = pgettext_lazy("Form state", "Work in progress")
        READY = pgettext_lazy("Form state", "Ready")
        DELETED = pgettext_lazy("Form state", "Deleted")
