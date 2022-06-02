from django.utils.translation import pgettext_lazy
from enumfields import Enum


class SearchClass(str, Enum):
    """
    In Finnish: Haun luokitus
    """

    PLOT_SEARCH = "plot_search"
    OTHER = "other_search"

    class Labels:
        PLOT_SEARCH = pgettext_lazy("Search class", "Plot search")
        OTHER = pgettext_lazy("Search class", "Other")


class InformationState(str, Enum):
    """
    In Finnish: Lisätiedon tila
    """

    CHECKED = "checked"
    NOT_NEEDED = "not_checked"
    FUTHER_ACTION = "futher_action"

    class Labels:
        CHECKED = pgettext_lazy("Information state", "Checked")
        NOT_NEEDED = pgettext_lazy("Information state", "Not needed")
        FUTHER_ACTION = pgettext_lazy("Information state", "Requires futher action")
