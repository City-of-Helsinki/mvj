from django.utils.translation import pgettext_lazy
from enumfields import Enum


class AreaSearchLessor(str, Enum):
    """
    In Finnish: Vuokranantaja
    """

    AKV = "AKV"
    MAKE = "MAKE"
    LIPA = "LIPA"
    UPA = "UPA"
    NUP = "NUP"

    class Labels:
        AKV = pgettext_lazy("Area search lessor", "Area use and control")
        MAKE = pgettext_lazy("Area search lessor", "Development of land assets")
        LIPA = pgettext_lazy("Area search lessor", "Sports venue services")
        UPA = pgettext_lazy("Area search lessor", "Outdoor services")
        NUP = pgettext_lazy("Area search lessor", "Youth services")


class SearchClass(str, Enum):
    """
    In Finnish: Haun luokitus
    """

    PLOT_SEARCH = "plot_search"
    OTHER = "other_search"

    class Labels:
        PLOT_SEARCH = pgettext_lazy("Search class", "Plot search")
        OTHER = pgettext_lazy("Search class", "Other")


class SearchStage(str, Enum):
    """
    In Finnish: Tonttihaun vaihe
    """

    IN_PREPARATION = "in_preparation"
    IN_ACTION = "in_action"
    PROCESSING = "processing"
    DECISION = "decision"
    SETTLED = "settled"

    class Labels:
        IN_PREPARATION = pgettext_lazy("Search stage", "In preparation")
        IN_ACTION = pgettext_lazy("Search stage", "In action")
        PROCESSING = pgettext_lazy("Search stage", "Processing")
        DECISION = pgettext_lazy("Search stage", "Decision making")
        SETTLED = pgettext_lazy("Search stage", "Settled")


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


class DeclineReason(str, Enum):
    """
    In Finnish: Hylkäyksen syy
    """

    APPLICATION_EXPIRED = "application_expired"
    APPLICATION_MISSED_DEADLINE = "application_missed_deadline"
    APPLICATION_MISSING_DETAILS = "application_missing_details"
    APPLICANT_NOT_QUALIFIED = "applicant_not_qualified"
    APPLICANT_WITHDREW_APPLICATION = "applicant_withdrew_application"
    NOT_IN_CONTROL = "not_in_control"
    NOT_AVAILABLE_LEASE = "not_available_for_lease"
    OTHER = "other"

    class Labels:
        APPLICATION_EXPIRED = pgettext_lazy("Decline reason", "Application expired")
        APPLICATION_MISSED_DEADLINE = pgettext_lazy(
            "Decline reason", "Application missed deadline"
        )
        APPLICATION_MISSING_DETAILS = pgettext_lazy(
            "Decline reason", "Application missing details"
        )
        APPLICANT_NOT_QUALIFIED = pgettext_lazy(
            "Decline reason", "Applicant not qualified"
        )
        APPLICANT_WITHDREW_APPLICATION = pgettext_lazy(
            "Decline reason", "Applicant withdrew application"
        )
        NOT_IN_CONTROL = pgettext_lazy("Decline reason", "Area not controlled by city")
        NOT_AVAILABLE_LEASE = pgettext_lazy(
            "Decline reason", "Area not available for lease"
        )
        OTHER = pgettext_lazy("Decline reason", "Other reason")


class AreaSearchState(str, Enum):
    """
    In Finnish: Aluehaun tila
    """

    RECEIVED = "received"
    PENDING_INFORMATION = "pending_information"
    IN_ACTION = "in_action"
    SETTLED = "settled"
    REVOKED = "revoked"
    DECLINED = "declined"

    class Labels:
        RECEIVED = pgettext_lazy("Area search state", "Received")
        PENDING_INFORMATION = pgettext_lazy(
            "Area search state", "Pending additional information"
        )
        IN_ACTION = pgettext_lazy("Area search state", "In action")
        SETTLED = pgettext_lazy("Area search state", "Settled")
        REVOKED = pgettext_lazy("Area search state", "Revoked")
        DECLINED = pgettext_lazy("Area search state", "Declined")


class RelatedPlotApplicationContentType(str, Enum):
    """
    In Finnish: Liittyvän tontti- tai aluehakemuksen sisältötyyppi
    """

    AREA_SEARCH = "areasearch"
    TARGET_STATUS = "targetstatus"
    PLOT_SEARCH = "plotsearch"

    @classmethod
    def choices(cls):
        return [(field.value, field.name) for field in cls]

    @classmethod
    def values(cls):
        return [field.value for field in cls]
