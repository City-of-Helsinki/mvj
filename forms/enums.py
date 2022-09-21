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


class SectionType(str, Enum):
    """
    In Finnish: Osion tyyppi
    """

    SHOW_ALWAYS = "show_always"
    SHOW_IF = "show_if"

    class Labels:
        SHOW_ALWAYS = pgettext_lazy("Section type", "Show always")
        SHOW_IF = pgettext_lazy("Section type", "Show if")


class ApplicantType(str, Enum):
    """
    In Finnish: Hakijan tyyppi
    """

    PERSON = "person"
    COMPANY = "company"
    BOTH = "both"

    class Labels:
        PERSON = pgettext_lazy("Applicant type", "Person")
        COMPANY = pgettext_lazy("Applicant type", "Company")
        BOTH = pgettext_lazy("Applicant type", "Both")
