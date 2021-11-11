from django.utils.translation import pgettext_lazy
from enumfields import Enum


class SearchClass(str, Enum):
    """
    In Finnish: Haun luokitus
    """

    PLOT_SEARCH = "plot_search"
    OTHER = "other_search"

    class Labels:
        PLOT_SEARCH = pgettext_lazy("Plot search", "Plot search")
        OTHER = pgettext_lazy("Plot search", "Other")
