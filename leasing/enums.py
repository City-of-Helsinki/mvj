from django.utils.translation import pgettext_lazy
from enumfields import Enum, IntEnum


class Classification(Enum):
    """
    In Finnish: Julkisuusluokka
    """

    PUBLIC = "public"
    CONFIDENTIAL = "confidential"
    OFFICIAL = "official"

    class Labels:
        PUBLIC = pgettext_lazy("Classification", "Public")
        CONFIDENTIAL = pgettext_lazy("Classification", "Confidential")
        OFFICIAL = pgettext_lazy("Classification", "Official")


class LeaseState(Enum):
    """
    In Finnish: Tila
    """

    LEASE = "lease"
    SHORT_TERM_LEASE = "short_term_lease"
    LONG_TERM_LEASE = "long_term_lease"
    RESERVATION = "reservation"
    RESERVE = "reserve"
    PERMISSION = "permission"
    TENURE = "tenure"
    RYA = "rya"
    POWER_OF_ATTORNEY = "power_of_attorney"
    PRELIMINARY = "preliminary"

    class Labels:
        LEASE = pgettext_lazy("Lease state", "Lease")
        SHORT_TERM_LEASE = pgettext_lazy("Lease state", "Short term lease")
        LONG_TERM_LEASE = pgettext_lazy("Lease state", "Long term lease")
        RESERVATION = pgettext_lazy("Lease state", "Reservation")
        RESERVE = pgettext_lazy("Lease state", "Reserve")
        PERMISSION = pgettext_lazy("Lease state", "Permission")
        TENURE = pgettext_lazy("Lease state", "Tenure")
        RYA = pgettext_lazy("Lease state", "Buildings and public areas")
        POWER_OF_ATTORNEY = pgettext_lazy("Lease state", "Power of attorney")
        PRELIMINARY = pgettext_lazy("Lease state", "Preliminary")


class LeaseRelationType(Enum):
    """
    In Finnish: Liittyvän vuokrauksen tyyppi
    """

    TRANSFER = "transfer"
    OTHER = "other"

    class Labels:
        TRANSFER = pgettext_lazy("Lease relation", "Transfer")
        OTHER = pgettext_lazy("Lease relation", "Other")


class NoticePeriodType(Enum):
    """
    In Finnish: Irtisanomisajan tyyppi
    """

    NO_PERIOD = "no_period"
    TIME_PERIOD = "time_period"
    OTHER = "other"

    class Labels:
        NO_PERIOD = pgettext_lazy("Notice period", "No period")
        TIME_PERIOD = pgettext_lazy("Notice period", "Time period")
        OTHER = pgettext_lazy("Notice period", "Other")


class TenantContactType(Enum):
    """
    In Finnish: Vuokralaisen yhteystiedon tyyppi
    """

    TENANT = "tenant"
    BILLING = "billing"
    CONTACT = "contact"

    class Labels:
        TENANT = pgettext_lazy("Tenant contact type", "Tenant")
        BILLING = pgettext_lazy("Tenant contact type", "Billing contact")
        CONTACT = pgettext_lazy("Tenant contact type", "Contact")


class LocationType(Enum):
    """
    In Finnish: Sijainti
    """

    SURFACE = "surface"
    UNDERGROUND = "underground"

    class Labels:
        SURFACE = pgettext_lazy("Location type", "Surface")
        UNDERGROUND = pgettext_lazy("Location type", "Underground")


class LeaseAreaType(Enum):
    """
    In Finnish: Vuokra-alueen tyyppi
    """

    PLAN_UNIT = "plan_unit"
    REAL_PROPERTY = "real_property"
    UNSEPARATED_PARCEL = "unseparated_parcel"
    OTHER = "other"

    class Labels:
        PLAN_UNIT = pgettext_lazy("Lease area type", "Plan unit")
        REAL_PROPERTY = pgettext_lazy("Lease area type", "Real property")
        UNSEPARATED_PARCEL = pgettext_lazy("Lease area type", "Unseparated parcel")
        OTHER = pgettext_lazy("Lease area type", "Other")


class LeaseAreaAttachmentType(Enum):
    """
    In Finnish: Liitetiedoston tyyppi
    """

    MATTI_REPORT = "matti_report"
    GEOTECHNICAL = "geotechnical"

    class Labels:
        MATTI_REPORT = pgettext_lazy("Lease area attachment type", "MATTI report")
        GEOTECHNICAL = pgettext_lazy("Lease area attachment type", "Geotechnical")


class PlotType(Enum):
    """
    In Finnish: Tontin tyyppi
    """

    REAL_PROPERTY = "real_property"
    UNSEPARATED_PARCEL = "unseparated_parcel"

    class Labels:
        REAL_PROPERTY = pgettext_lazy("Plot type", "Real property")
        UNSEPARATED_PARCEL = pgettext_lazy("Plot type", "Unseparated parcel")


class PlotSearchTargetType(Enum):
    """
    In Finnish: Tonttihaun kohdetyypit
    """

    SEARCHABLE = "searchable"
    PROCEDURAL_RESERVATION = "procedural_reservation"
    DIRECT_RESERVATION = "direct_reservation"

    class Labels:
        SEARCHABLE = pgettext_lazy("Plot type", "Searchable")
        PROCEDURAL_RESERVATION = pgettext_lazy("Plot type", "Procedural reservation")
        DIRECT_RESERVATION = pgettext_lazy("Plot type", "Direct reservation")


class PeriodType(Enum):
    """
    In Finnish: Yksikkö (aika)
    """

    PER_MONTH = "per_month"
    PER_YEAR = "per_year"

    class Labels:
        PER_MONTH = pgettext_lazy("Period type", "/ month")
        PER_YEAR = pgettext_lazy("Period type", "/ year")


class AreaUnit(Enum):
    """
    In Finnish: Yksikkö (alue)
    """

    # In Finnish: Neliömetri
    SQUARE_METRE = "m2"
    # In Finnish: Kerrosneliömetri
    FLOOR_SQUARE_METRE = "kem2"
    # In Finnish: Huoneistoneliömetri
    APARTMENT_SQUARE_METRE = "hm2"

    class Labels:
        SQUARE_METRE = pgettext_lazy("Area unit", "m^2")
        FLOOR_SQUARE_METRE = pgettext_lazy("Area unit", "Floor area m^2")
        APARTMENT_SQUARE_METRE = pgettext_lazy("Area unit", "Apartment area m^2")


class ConstructabilityState(Enum):
    """
    In Finnish: Selvitysaste
    """

    UNVERIFIED = "unverified"
    REQUIRES_MEASURES = "requires_measures"
    ENQUIRY_SENT = "enquiry_sent"
    COMPLETE = "complete"

    class Labels:
        UNVERIFIED = pgettext_lazy("Constructability state", "Unverified")
        REQUIRES_MEASURES = pgettext_lazy("Constructability state", "Requires measures")
        ENQUIRY_SENT = pgettext_lazy("Constructability state", "Enquiry sent")
        COMPLETE = pgettext_lazy("Constructability state", "Complete")


class ConstructabilityType(Enum):
    """
    In Finnish: Rakentamiskelpoisuusselitteen tyyppi
    """

    PRECONSTRUCTION = "preconstruction"
    DEMOLITION = "demolition"
    POLLUTED_LAND = "polluted_land"
    REPORT = "report"
    OTHER = "other"

    class Labels:
        PRECONSTRUCTION = pgettext_lazy("Constructability type", "Preconstruction")
        DEMOLITION = pgettext_lazy("Constructability type", "Demolition")
        POLLUTED_LAND = pgettext_lazy("Constructability type", "Polluted land")
        REPORT = pgettext_lazy("Constructability type", "Report")
        OTHER = pgettext_lazy("Constructability type", "Other")


class PollutedLandRentConditionState(Enum):
    """
    In Finnish: Vuokraehtojen kysymisen tyyppi
    """

    ASKED = "asked"
    READY = "ready"

    class Labels:
        ASKED = pgettext_lazy("Polluted Land rent condition state", "Asked")
        READY = pgettext_lazy("Polluted Land rent condition state", "Ready")


class ConstructabilityReportInvestigationState(Enum):
    """
    In Finnish: Rakennettavuusselvityksen tila
    """

    NO_NEED = "no_need"
    ONGOING = "ongoing"
    READY = "ready"

    class Labels:
        NO_NEED = pgettext_lazy(
            "Constructability Report investigation state", "No need"
        )
        ONGOING = pgettext_lazy(
            "Constructability Report investigation state", "Ongoing"
        )
        READY = pgettext_lazy("Constructability Report investigation state", "Ready")


class RentType(Enum):
    """
    In Finnish: Vuokralaji
    """

    INDEX2022 = "index2022"  # Indeksi
    INDEX = "index"  # Indeksi (Vanha)
    ONE_TIME = "one_time"  # Kertakaikkinen
    FIXED = "fixed"  # Kiinteä
    FREE = "free"  # Korvauksetta
    MANUAL = "manual"  # Käsinlaskenta

    class Labels:
        INDEX2022 = pgettext_lazy("Rent type", "Index")
        INDEX = pgettext_lazy("Rent type", "Index (old)")
        ONE_TIME = pgettext_lazy("Rent type", "One time")
        FIXED = pgettext_lazy("Rent type", "Fixed")
        FREE = pgettext_lazy("Rent type", "Free")
        MANUAL = pgettext_lazy("Rent type", "Manual")


class RentCycle(Enum):
    """
    In Finnish: Vuokrakausi
    """

    JANUARY_TO_DECEMBER = "january_to_december"
    APRIL_TO_MARCH = "april_to_march"

    class Labels:
        JANUARY_TO_DECEMBER = pgettext_lazy("Rent cycle", "January to december")
        APRIL_TO_MARCH = pgettext_lazy("Rent cycle", "April to march")


class IndexType(Enum):
    """
    In Finnish: Indeksin tunnusnumero
    """

    TYPE_1 = "type_1"
    TYPE_2 = "type_2"
    TYPE_3 = "type_3"
    TYPE_4 = "type_4"
    TYPE_5 = "type_5"
    TYPE_6 = "type_6"
    TYPE_7 = "type_7"

    class Labels:
        TYPE_1 = pgettext_lazy("Index type", "ind 50620 / 10/20%:n vaihtelut")
        TYPE_2 = pgettext_lazy("Index type", "ind 4661 / 10/20%:n vaihtelut")
        TYPE_3 = pgettext_lazy("Index type", "ind 418 / 10%:n vaihtelu")
        TYPE_4 = pgettext_lazy("Index type", "ind 418 / 20%:n vaihtelu")
        TYPE_5 = pgettext_lazy("Index type", "ind 392")
        TYPE_6 = pgettext_lazy("Index type", "ind 100 (pyöristys)")
        TYPE_7 = pgettext_lazy("Index type", "ind 100")


class DueDatesType(Enum):
    """
    In Finnish: Laskutusjako
    """

    CUSTOM = "custom"
    FIXED = "fixed"

    class Labels:
        CUSTOM = pgettext_lazy("Due dates type", "Custom")
        FIXED = pgettext_lazy("Due dates type", "Fixed")


class DueDatesPosition(Enum):
    """
    In Finnish: Eräpäivän sijainti
    """

    START_OF_MONTH = "start_of_month"
    MIDDLE_OF_MONTH = "middle_of_month"

    class Labels:
        START_OF_MONTH = pgettext_lazy("Due dates position", "Start of month")
        MIDDLE_OF_MONTH = pgettext_lazy("Due dates position", "Middle of month")


class RentAdjustmentType(Enum):
    """
    In Finnish: Alennus/Korotus
    """

    DISCOUNT = "discount"
    INCREASE = "increase"

    class Labels:
        DISCOUNT = pgettext_lazy("Rent adjustment type", "Discount")
        INCREASE = pgettext_lazy("Rent adjustment type", "Increase")


class RentAdjustmentAmountType(Enum):
    """
    In Finnish: Määrän tyyppi
    """

    PERCENT_PER_YEAR = "percent_per_year"
    AMOUNT_PER_YEAR = "amount_per_year"
    AMOUNT_TOTAL = "amount_total"

    class Labels:
        PERCENT_PER_YEAR = pgettext_lazy("Rent Adjustment amount type", "% per year")
        AMOUNT_PER_YEAR = pgettext_lazy("Rent Adjustment amount type", "€ per year")
        AMOUNT_TOTAL = pgettext_lazy("Rent Adjustment amount type", "€ total")


class SubventionType(Enum):
    """
    In Finnish: Subvention tyyppi
    """

    FORM_OF_MANAGEMENT = "form_of_management"  # In Finnish: Hallintamuoto
    RE_LEASE = "re_lease"  # In Finnish: Uudelleenvuokraus

    class Labels:
        FORM_OF_MANAGEMENT = pgettext_lazy("Subvention type", "Form of management")
        RE_LEASE = pgettext_lazy("Subvention type", "Re-lease")


class InvoiceDeliveryMethod(Enum):
    """
    In Finnish: E vai paperilasku
    """

    MAIL = "mail"
    ELECTRONIC = "electronic"

    class Labels:
        MAIL = pgettext_lazy("Invoice delivery method", "Mail")
        ELECTRONIC = pgettext_lazy("Invoice delivery method", "Electronic")


class InvoiceState(Enum):
    """
    In Finnish: Laskun tila
    """

    OPEN = "open"
    PAID = "paid"
    REFUNDED = "refunded"

    class Labels:
        OPEN = pgettext_lazy("Invoice state", "Open")
        PAID = pgettext_lazy("Invoice state", "Paid")
        REFUNDED = pgettext_lazy("Invoice state", "Refunded")


class InvoiceType(Enum):
    """
    In Finnish: Laskun tyyppi
    """

    CHARGE = "charge"
    CREDIT_NOTE = "credit_note"

    class Labels:
        CHARGE = pgettext_lazy("Invoice type", "Charge")
        CREDIT_NOTE = pgettext_lazy("Invoice type", "Credit note")


class ContactType(Enum):
    """
    In Finnish: Yhteystiedon tyyppi
    """

    PERSON = "person"
    BUSINESS = "business"
    UNIT = "unit"
    ASSOCIATION = "association"
    OTHER = "other"

    class Labels:
        PERSON = pgettext_lazy("Contact type", "Person")
        BUSINESS = pgettext_lazy("Contact type", "Business")
        UNIT = pgettext_lazy("Contact type", "Unit")
        ASSOCIATION = pgettext_lazy("Contact type", "Association")
        OTHER = pgettext_lazy("Contact type", "Other")


class InfillDevelopmentCompensationState(Enum):
    """
    In Finnish: Täydennysrakentamiskorvauksen neuvotteluvaihe
    """

    ONGOING = "ongoing"
    NEGOTIATING = "negotiating"
    DECISION = "decision"

    class Labels:
        ONGOING = pgettext_lazy("Infill development compensation", "Ongoing")
        NEGOTIATING = pgettext_lazy("Infill development compensation", "Negotiating")
        DECISION = pgettext_lazy("Infill development compensation", "Decision")


class AreaType(Enum):
    """
    In Finnish: Alueen tyyppi
    """

    LEASE_AREA = "lease_area"  # Vuokra-alue
    PLAN_UNIT = "plan_unit"  # Kaavayksikkö
    REAL_PROPERTY = "real_property"  # Kiinteistö
    UNSEPARATED_PARCEL = "unseparated_parcel"  # Määräala
    PLOT_DIVISION = "plot_division"  # Tonttijako
    BASIS_OF_RENT = "basis_of_rent"  # Vuokrausperiaate
    INFILL_DEVELOPMENT_COMPENSATION = (
        "infill_development_compensation"  # Täydennysrakentamiskorvaus
    )
    LAND_USE_AGREEMENT = "land_use_agreement"  # Maankäyttösopimus
    DETAILED_PLAN = "detailed_plan"  # Voimassa oleva asemakaava
    PRE_DETAILED_PLAN = "pre_detailed_plan"  # Vireillä tai tuleva asemakaava
    OTHER = "other"

    class Labels:
        LEASE_AREA = pgettext_lazy("Area type", "Lease area")
        PLAN_UNIT = pgettext_lazy("Area type", "Plan unit")
        REAL_PROPERTY = pgettext_lazy("Area type", "Real property")
        UNSEPARATED_PARCEL = pgettext_lazy("Area type", "Unseparated parcel")
        PLOT_DIVISION = pgettext_lazy("Area type", "Plot division")
        BASIS_OF_RENT = pgettext_lazy("Area type", "Basis of rent")
        INFILL_DEVELOPMENT_COMPENSATION = pgettext_lazy(
            "Area type", "Infill development compensation"
        )
        LAND_USE_AGREEMENT = pgettext_lazy("Area type", "Land use agreement")
        DETAILED_PLAN = pgettext_lazy("Area type", "Detailed plan")
        OTHER = pgettext_lazy("Area type", "Other")


class EmailLogType(str, Enum):
    """
    In Finnish: Sähköpostilokin tyyppi
    """

    CONSTRUCTABILITY = "constructability"

    class Labels:
        CONSTRUCTABILITY = pgettext_lazy("Email log type", "Constructability")


class LeaseholdTransferPartyType(Enum):
    """
    In Finnish: Vuokraoikeuden siirron osapuolen tyyppi
    """

    LESSOR = "lessor"  # Vuokranantaja
    CONVEYOR = "conveyor"  # Luovuttaja
    ACQUIRER = "acquirer"  # Vuokralainen

    class Labels:
        LESSOR = pgettext_lazy("Leasehold transfer party type", "Lessor")
        CONVEYOR = pgettext_lazy("Leasehold transfer party type", "Conveyor")
        ACQUIRER = pgettext_lazy("Leasehold transfer party type", "Acquirer")


class DecisionTypeKind(Enum):
    """
    In Finnish: Päätöksen tyypin laji
    """

    LEASE_CANCELLATION = "lease_cancellation"  # Vuokrasopimuksen purkaminen
    BASIS_OF_RENT = "basis_of_rent"  # Vuokrausperiaate
    LEASE_SERVICE_UNIT_TRANSFER = (
        "lease_service_unit_transfer"  # Vuokrauksen siirto palvelukokonaisuudelle
    )

    class Labels:
        LEASE_CANCELLATION = pgettext_lazy("Decision type kind", "Lease cancellation")
        BASIS_OF_RENT = pgettext_lazy("Decision type kind", "Basis of Rent")
        LEASE_SERVICE_UNIT_TRANSFER = pgettext_lazy(
            "Decision type kind", "Lease service unit transfer"
        )


class DetailedPlanClass(Enum):
    """
    In Finnish: Asemakaavan luokka
    """

    PENDING = "pending"
    EFFECTIVE = "effective"

    class Labels:
        PENDING = pgettext_lazy("Detailed plan class", "Pending")
        EFFECTIVE = pgettext_lazy("Detailed plan class", "Effective")


class BasisOfRentType(Enum):
    """
    In Finnish: Vuokraperusteen tyyppi
    """

    LEASE2022 = "lease2022"  # In Finnish: Vuokra
    LEASE = "lease"  # In Finnish: Vuokra (Vanha)
    TEMPORARY = "temporary"  # In Finnish: Tilapäinen
    ADDITIONAL_YARD = "additional_yard"  # In Finnish: Lisäpiha
    FIELD = "field"  # In Finnish: Pelto
    MAST = "mast"  # In Finnish: Masto

    class Labels:
        LEASE2022 = pgettext_lazy("Basis of rent type", "Lease")
        LEASE = pgettext_lazy("Basis of rent type", "Lease (old)")
        TEMPORARY = pgettext_lazy("Basis of rent type", "Temporary")
        ADDITIONAL_YARD = pgettext_lazy("Basis of rent type", "Additional yard")
        FIELD = pgettext_lazy("Basis of rent type", "Field")
        MAST = pgettext_lazy("Basis of rent type", "Mast")


class BasisOfRentZone(Enum):
    """
    In Finnish: Vyöhyke
    """

    ZONE_1 = "zone_1"
    ZONE_2 = "zone_2"
    ZONE_3 = "zone_3"

    class Labels:
        ZONE_1 = pgettext_lazy("Basis of rent zone", "Zone 1")
        ZONE_2 = pgettext_lazy("Basis of rent zone", "Zone 2")
        ZONE_3 = pgettext_lazy("Basis of rent zone", "Zone 3")


class LandUseContractType(Enum):
    """
    In Finnish: Maankäyttösopimus tyyppi
    """

    LAND_USE_AGREEMENT = "Land use agreement"
    AGREEMENT_ON_APPRECIATION = "Agreement on appreciation"
    NO_AGREEMENT = "No agreement"

    class Labels:
        LAND_USE_AGREEMENT = pgettext_lazy(
            "Land Use Contract Type", "Land use agreement"
        )
        AGREEMENT_ON_APPRECIATION = pgettext_lazy(
            "Land Use Contract Type", "Agreement on appreciation"
        )
        NO_AGREEMENT = pgettext_lazy("Land Use Contract Type", "No agreement")


class LandUseAgreementAttachmentType(Enum):
    """
    In Finnish: Maankäyttösopimuksen liitetiedoston tyyppi
    """

    GENERAL = "general"
    COMPENSATION_CALCULATION = "compensation_calculation"

    class Labels:
        GENERAL = pgettext_lazy("Land use agreement attachment type", "General")
        COMPENSATION_CALCULATION = pgettext_lazy(
            "Land use agreement attachment type", "Compensation calculation"
        )


class LandUseAgreementLitigantContactType(Enum):
    """
    In Finnish: Maankäyttösopimuksen osapuolen yhteystiedon tyyppi
    """

    TENANT = "tenant"
    BILLING = "billing"

    class Labels:
        TENANT = pgettext_lazy("Land Use Agreement Litigant Contact Type", "Tenant")
        BILLING = pgettext_lazy("Land Use Agreement Litigant Contact Type", "Billing")


class PlanUnitStatus(Enum):
    """
    In Finnish: Kaavayksikön tila
    """

    PRESENT = "present"
    PENDING = "pending"

    class Labels:
        PRESENT = pgettext_lazy("Plan Unit Status", "Present")
        PENDING = pgettext_lazy("Plan Unit Status", "Pending")


class ServiceUnitId(IntEnum):
    """
    In Finnish: Palvelukokonaisuuden tunniste

    Expected IDs of the ServiceUnit model in fixtures and database.
    """

    MAKE = 1
    AKV = 2
    KUVA_LIPA = 3
    KUVA_UPA = 4
    KUVA_NUP = 5

    class Labels:
        MAKE = "Maaomaisuuden kehittäminen ja tontit"
        AKV = "Alueiden käyttö ja valvonta"
        KUVA_LIPA = "KuVa / Liikuntapaikkapalvelut"
        KUVA_UPA = "KuVa / Ulkoilupalvelut"
        KUVA_NUP = "KuVa / Nuorisopalvelut"


class SapSalesOfficeNumber(Enum):
    """
    In Finnish: SAP myyntitoimiston numero

    These are set to lessor contacts in
    leasing>management>commands>set_default_lessors.py
    """

    MAKE = "2826"
    AKV = "2805"
    KUVA = "2951"


class SapSalesOrgNumber(Enum):
    """
    In Finnish: SAP myyntiorganisaation numero

    Make's number was initialized in leasing migration 0063, and I assume others
    have been added to the database later via the service_unit.json fixture.
    """

    MAKE = "2800"
    AKV = "2800"
    KUVA = "2900"


class PeriodicRentAdjustmentType(Enum):
    """
    In Finnish: Tasotarkistuksen tyyppi

    The rents that have an old_dwellings_in_housing_companies_price_index
    also have assigned to them the type of the index that is used to calculate
    the interval of the old_dwellings_in_housing_companies_price_index check
    of the rent price.
    """

    TASOTARKISTUS_20_20 = "TASOTARKISTUS_20_20"
    TASOTARKISTUS_20_10 = "TASOTARKISTUS_20_10"

    class Labels:
        TASOTARKISTUS_20_20 = pgettext_lazy(
            "Periodic Rent Adjustment Type",
            "Periodic Rent Adjustment 20y/20y",
        )
        TASOTARKISTUS_20_10 = pgettext_lazy(
            "Periodic Rent Adjustment Type",
            "Periodic Rent Adjustment 20y/10y",
        )
