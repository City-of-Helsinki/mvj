from django.utils.translation import pgettext_lazy
from enumfields import Enum


class Classification(Enum):
    """
    In Finnish: Julkisuusluokka
    """
    PUBLIC = 'public'
    CONFIDENTIAL = 'confidential'
    OFFICIAL = 'official'

    class Labels:
        PUBLIC = pgettext_lazy('Classification', 'Public')
        CONFIDENTIAL = pgettext_lazy('Classification', 'Confidential')
        OFFICIAL = pgettext_lazy('Classification', 'Official')


class LeaseState(Enum):
    """
    In Finnish: Tila
    """
    LEASE = 'lease'
    RESERVATION = 'reservation'
    RESERVE = 'reserve'
    PERMISSION = 'permission'
    TRANSFERRED = 'transferred'
    APPLICATION = 'application'
    FREE = 'free'

    class Labels:
        LEASE = pgettext_lazy('Lease state', 'Lease')
        RESERVATION = pgettext_lazy('Lease state', 'Reservation')
        RESERVE = pgettext_lazy('Lease state', 'Reserve')
        PERMISSION = pgettext_lazy('Lease state', 'Permission')
        TRANSFERRED = pgettext_lazy('Lease state', 'Transferred')
        APPLICATION = pgettext_lazy('Lease state', 'Application')
        FREE = pgettext_lazy('Lease state', 'Free')


class LeaseRelationType(Enum):
    """
    In Finnish: Liittyvän vuokrauksen tyyppi
    """
    TRANSFER = 'transfer'

    class Labels:
        TRANSFER = pgettext_lazy('Lease relation', 'Transfer')


class NoticePeriodType(Enum):
    """
    In Finnish: Irtisanomisajan tyyppi
    """
    NO_PERIOD = 'no_period'
    TIME_PERIOD = 'time_period'
    OTHER = 'other'

    class Labels:
        NO_PERIOD = pgettext_lazy('Notice period', 'No period')
        TIME_PERIOD = pgettext_lazy('Notice period', 'Time period')
        OTHER = pgettext_lazy('Notice period', 'Other')


class TenantContactType(Enum):
    """
    In Finnish: Vuokralaisen yhteystiedon tyyppi
    """
    TENANT = 'tenant'
    BILLING = 'billing'
    CONTACT = 'contact'

    class Labels:
        TENANT = pgettext_lazy('Tenant contact type', 'Tenant')
        BILLING = pgettext_lazy('Tenant contact type', 'Billing contact')
        CONTACT = pgettext_lazy('Tenant contact type', 'Contact')


class LocationType(Enum):
    """
    In Finnish: Sijainti
    """
    SURFACE = 'surface'
    UNDERGROUND = 'underground'

    class Labels:
        SURFACE = pgettext_lazy('Location type', 'Surface')
        UNDERGROUND = pgettext_lazy('Location type', 'Underground')


class LeaseAreaType(Enum):
    """
    In Finnish: Vuokra-alueen tyyppi
    """
    PLAN_UNIT = 'plan_unit'
    REAL_PROPERTY = 'real_property'
    UNSEPARATED_PARCEL = 'unseparated_parcel'
    OTHER = 'other'

    class Labels:
        PLAN_UNIT = pgettext_lazy('Lease area type', 'Plan unit')
        REAL_PROPERTY = pgettext_lazy('Lease area type', 'Real property')
        UNSEPARATED_PARCEL = pgettext_lazy('Lease area type', 'Unseparated parcel')
        OTHER = pgettext_lazy('Lease area type', 'Other')


class PlotType(Enum):
    """
    In Finnish: Tontin tyyppi
    """
    REAL_PROPERTY = 'real_property'
    UNSEPARATED_PARCEL = 'unseparated_parcel'

    class Labels:
        REAL_PROPERTY = pgettext_lazy('Plot type', 'Real property')
        UNSEPARATED_PARCEL = pgettext_lazy('Plot type', 'Unseparated parcel')


class PeriodType(Enum):
    """
    In Finnish: Yksikkö
    """
    PER_MONTH = 'per_month'
    PER_YEAR = 'per_year'

    class Labels:
        PER_MONTH = pgettext_lazy('Period type', '/ month')
        PER_YEAR = pgettext_lazy('Period type', '/ year')


class ConstructabilityState(Enum):
    """
    In Finnish: Selvitysaste
    """
    UNVERIFIED = 'unverified'
    REQUIRES_MEASURES = 'requires_measures'
    COMPLETE = 'complete'

    class Labels:
        UNVERIFIED = pgettext_lazy('Constructability state', 'Unverified')
        REQUIRES_MEASURES = pgettext_lazy('Constructability state', 'Requires measures')
        COMPLETE = pgettext_lazy('Constructability state', 'Complete')


class ConstructabilityType(Enum):
    """
    In Finnish: Rakentamiskelpoisuusselitteen tyyppi
    """
    PRECONSTRUCTION = 'preconstruction'
    DEMOLITION = 'demolition'
    POLLUTED_LAND = 'polluted_land'
    REPORT = 'report'
    OTHER = 'other'

    class Labels:
        PRECONSTRUCTION = pgettext_lazy('Constructability type', 'Preconstruction')
        DEMOLITION = pgettext_lazy('Constructability type', 'Demolition')
        POLLUTED_LAND = pgettext_lazy('Constructability type', 'Polluted land')
        REPORT = pgettext_lazy('Constructability type', 'Report')
        OTHER = pgettext_lazy('Constructability type', 'Other')


class PollutedLandRentConditionState(Enum):
    """
    In Finnish: Vuokraehtojen kysymisen tyyppi
    """
    ASKED = 'asked'
    READY = 'ready'

    class Labels:
        ASKED = pgettext_lazy('Polluted Land rent condition state', 'Asked')
        READY = pgettext_lazy('Polluted Land rent condition state', 'Ready')


class ConstructabilityReportInvestigationState(Enum):
    """
    In Finnish: Rakennettavuusselvityksen tila
    """
    NO_NEED = 'no_need'
    ONGOING = 'ongoing'
    READY = 'ready'

    class Labels:
        NO_NEED = pgettext_lazy('Constructability Report investigation state', 'No need')
        ONGOING = pgettext_lazy('Constructability Report investigation state', 'Ongoing')
        READY = pgettext_lazy('Constructability Report investigation state', 'Ready')


class RentType(Enum):
    """
    In Finnish: Vuokralaji
    """
    INDEX = 'index'
    ONE_TIME = 'one_time'
    FIXED = 'fixed'
    FREE = 'free'
    MANUAL = 'manual'

    class Labels:
        INDEX = pgettext_lazy('Rent type', 'Index')
        ONE_TIME = pgettext_lazy('Rent type', 'One time')
        FIXED = pgettext_lazy('Rent type', 'Fixed')
        FREE = pgettext_lazy('Rent type', 'Free')
        MANUAL = pgettext_lazy('Rent type', 'Manual')


class RentCycle(Enum):
    """
    In Finnish: Vuokrakausi
    """
    JANUARY_TO_DECEMBER = 'january_to_december'
    APRIL_TO_MARCH = 'april_to_march'

    class Labels:
        JANUARY_TO_DECEMBER = pgettext_lazy('Rent cycle', 'January to december')
        APRIL_TO_MARCH = pgettext_lazy('Rent cycle', 'April to march')


class IndexType(Enum):
    """
    In Finnish: Indeksin tunnusnumero
    """
    TYPE_1 = 'type_1'
    TYPE_2 = 'type_2'
    TYPE_3 = 'type_3'
    TYPE_4 = 'type_4'
    TYPE_5 = 'type_5'
    TYPE_6 = 'type_6'
    TYPE_7 = 'type_7'

    class Labels:
        TYPE_1 = pgettext_lazy('Index type', 'ind 50620 / 10/20%:n vaihtelut')
        TYPE_2 = pgettext_lazy('Index type', 'ind 4661 / 10/20%:n vaihtelut')
        TYPE_3 = pgettext_lazy('Index type', 'ind 418 / 10%:n vaihtelu')
        TYPE_4 = pgettext_lazy('Index type', 'ind 418 / 20%:n vaihtelu')
        TYPE_5 = pgettext_lazy('Index type', 'ind 392')
        TYPE_6 = pgettext_lazy('Index type', 'ind 100 (pyöristys)')
        TYPE_7 = pgettext_lazy('Index type', 'ind 100')


class DueDatesType(Enum):
    """
    In Finnish: Laskutusjako
    """
    CUSTOM = 'custom'
    FIXED = 'fixed'

    class Labels:
        CUSTOM = pgettext_lazy('Due dates type', 'Custom')
        FIXED = pgettext_lazy('Due dates type', 'Fixed')


class DueDatesPosition(Enum):
    START_OF_MONTH = 'start_of_month'
    MIDDLE_OF_MONTH = 'middle_of_month'

    class Labels:
        START_OF_MONTH = pgettext_lazy('Due dates position', 'Start of month')
        MIDDLE_OF_MONTH = pgettext_lazy('Due dates position', 'Middle of month')


class RentAdjustmentType(Enum):
    DISCOUNT = 'discount'
    INCREASE = 'increase'

    class Labels:
        DISCOUNT = pgettext_lazy('Rent adjustment type', 'Discount')
        INCREASE = pgettext_lazy('Rent adjustment type', 'Increase')


class RentAdjustmentAmountType(Enum):
    PERCENT_PER_YEAR = 'percent_per_year'
    AMOUNT_PER_YEAR = 'amount_per_year'
    AMOUNT_TOTAL = 'amount_total'

    class Labels:
        PERCENT_PER_YEAR = pgettext_lazy('Rent Adjustment amount type', '% per year')
        AMOUNT_PER_YEAR = pgettext_lazy('Rent Adjustment amount type', '€ per year')
        AMOUNT_TOTAL = pgettext_lazy('Rent Adjustment amount type', '€ total')


class InvoiceDeliveryMethod(Enum):
    MAIL = 'mail'
    ELECTRONIC = 'electronic'

    class Labels:
        MAIL = pgettext_lazy('Invoice delivery method', 'Mail')
        ELECTRONIC = pgettext_lazy('Invoice delivery method', 'Electronic')


class InvoiceState(Enum):
    OPEN = 'open'
    PAID = 'paid'
    REFUNDED = 'refunded'

    class Labels:
        OPEN = pgettext_lazy('Invoice state', 'Open')
        PAID = pgettext_lazy('Invoice state', 'Paid')
        REFUNDED = pgettext_lazy('Invoice state', 'Refunded')


class InvoiceType(Enum):
    CHARGE = 'charge'
    CREDIT_NOTE = 'credit_note'

    class Labels:
        CHARGE = pgettext_lazy('Invoice type', 'Charge')
        CREDIT_NOTE = pgettext_lazy('Invoice type', 'Credit note')


class ContactType(Enum):
    PERSON = 'person'
    BUSINESS = 'business'
    UNIT = 'unit'
    ASSOCIATION = 'association'
    OTHER = 'other'

    class Labels:
        PERSON = pgettext_lazy('Contact type', 'Person')
        BUSINESS = pgettext_lazy('Contact type', 'Business')
        UNIT = pgettext_lazy('Contact type', 'Unit')
        ASSOCIATION = pgettext_lazy('Contact type', 'Association')
        OTHER = pgettext_lazy('Contact type', 'Other')
