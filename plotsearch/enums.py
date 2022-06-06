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
    NOT_CHECKED = "not_checked"
    NOT_NEEDED = "not_needed"
    FURTHER_ACTION = "further_action"

    class Labels:
        CHECKED = pgettext_lazy("Information state", "Checked")
        NOT_CHECKED = pgettext_lazy("Information state", "Not checked")
        NOT_NEEDED = pgettext_lazy("Information state", "Not needed")
        FURTHER_ACTION = pgettext_lazy("Information state", "Requires further action")


class InformationCheckName(str, Enum):
    """
    In Finnish: Lisätiedon nimi
    """

    TRADE_REGISTER = "trade_register"
    CREDITWORTHINESS = "creditworthiness"
    PENSION_CONTRIBUTIONS = "pension_contributions"
    VAT_REGISTER = "vat_register"
    ADVANCE_PAYMENT = "advance_payment"
    TAX_DEBT = "tax_debt"
    EMPLOYER_REGISTER = "employer_register"

    class Labels:
        TRADE_REGISTER = pgettext_lazy(
            "Information check name", "Trade register extract"
        )
        CREDITWORTHINESS = pgettext_lazy(
            "Information check name", "Creditworthiness certificate"
        )
        PENSION_CONTRIBUTIONS = pgettext_lazy(
            "Information check name",
            "Statement of payment of earning-related pension contributions",
        )
        VAT_REGISTER = pgettext_lazy(
            "Information check name", "Certificate of entry in the VAT register"
        )
        ADVANCE_PAYMENT = pgettext_lazy(
            "Information check name",
            "Certificate of entry in the advance payment register",
        )
        TAX_DEBT = pgettext_lazy("Information check name", "Tax debt certificate")
        EMPLOYER_REGISTER = pgettext_lazy(
            "Information check name",
            "Certificate of entry in the register of employers",
        )
