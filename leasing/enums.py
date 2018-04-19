from django.utils.translation import ugettext_lazy as _
from enumfields import Enum


class Classification(Enum):
    """
    In Finnish: Julkisuusluokka
    """
    PUBLIC = 'public'
    CONFIDENTIAL = 'confidential'
    OFFICIAL = 'official'

    class Labels:
        PUBLIC = _('Public')
        CONFIDENTIAL = _('Confidential')
        OFFICIAL = _('Official')


class LeaseState(Enum):
    """
    In Finnish: Tila
    """
    LEASE = 'lease'
    RESERVATION = 'reservation'
    PERMISSION = 'permission'
    TRANSFERRED = 'transferred'
    APPLICATION = 'application'
    FREE = 'free'

    class Labels:
        LEASE = _('Lease')
        RESERVATION = _('Reservation')
        PERMISSION = _('Permission')
        TRANSFERRED = _('Transferred')
        APPLICATION = _('Application')
        FREE = _('Free')


class LeaseRelationType(Enum):
    """
    In Finnish: Liittyvän vuokrauksen tyyppi
    """
    TRANSFER = 'transfer'

    class Labels:
        TRANSFER = _('Transfer')


class NoticePeriodType(Enum):
    """
    In Finnish: Irtisanomisajan tyyppi
    """
    NO_PERIOD = 'no_period'
    TIME_PERIOD = 'time_period'
    OTHER = 'other'

    class Labels:
        NO_PERIOD = _('No period')
        TIME_PERIOD = _('Time period')
        OTHER = _('Other')


class TenantContactType(Enum):
    """
    In Finnish: Vuokralaisen yhteystiedon tyyppi
    """
    TENANT = 'tenant'
    BILLING = 'billing'
    CONTACT = 'contact'

    class Labels:
        TENANT = _("Tenant")
        BILLING = _("Billing contact")
        CONTACT = _("Contact")


class LocationType(Enum):
    """
    In Finnish: Sijainti
    """
    SURFACE = 'surface'
    UNDERGROUND = 'underground'

    class Labels:
        SURFACE = _('Surface')
        UNDERGROUND = _('Underground')


class LeaseAreaType(Enum):
    """
    In Finnish: Vuokra-alueen tyyppi
    """
    PLAN_UNIT = 'plan_unit'
    REAL_PROPERTY = 'real_property'
    UNSEPARATED_PARCEL = 'unseparated_parcel'
    OTHER = 'other'

    class Labels:
        PLAN_UNIT = _('Plan unit')
        REAL_PROPERTY = _('Real property')
        UNSEPARATED_PARCEL = _('Unseparated parcel')
        OTHER = _('Other')


class PlotType(Enum):
    """
    In Finnish: Tontin tyyppi
    """
    REAL_PROPERTY = 'real_property'
    UNSEPARATED_PARCEL = 'unseparated_parcel'

    class Labels:
        REAL_PROPERTY = _('Real property')
        UNSEPARATED_PARCEL = _('Unseparated parcel')


class PeriodType(Enum):
    """
    In Finnish: Yksikkö
    """
    PER_MONTH = 'per_month'
    PER_YEAR = 'per_year'

    class Labels:
        PER_MONTH = _('/ month')
        PER_YEAR = _('/ year')


class ConstructabilityState(Enum):
    """
    In Finnish: Selvitysaste
    """
    UNVERIFIED = 'unverified'
    REQUIRES_MEASURES = 'requires_measures'
    COMPLETE = 'complete'

    class Labels:
        UNVERIFIED = _('Unverified')
        REQUIRES_MEASURES = _('Requires measures')
        COMPLETE = _('Complete')


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
        PRECONSTRUCTION = _('Preconstruction')
        DEMOLITION = _('Demolition')
        POLLUTED_LAND = _('Polluted land')
        REPORT = _('Report')
        OTHER = _('Other')


class PollutedLandRentConditionState(Enum):
    """
    In Finnish: Vuokraehtojen kysymisen tyyppi
    """
    ASKED = 'asked'
    READY = 'ready'

    class Labels:
        ASKED = _('Asked')
        READY = _('Ready')


class ConstructabilityReportInvestigationState(Enum):
    """
    In Finnish: Rakennettavuusselvityksen tila
    """
    NO_NEED = 'no_need'
    ONGOING = 'ongoing'
    READY = 'ready'

    class Labels:
        NO_NEED = _('No need')
        ONGOING = _('Ongoing')
        READY = _('Ready')


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
        INDEX = _('Index')
        ONE_TIME = _('One time')
        FIXED = _('Fixed')
        FREE = _('Free')
        MANUAL = _('Manual')


class RentCycle(Enum):
    """
    In Finnish: Vuokrakausi
    """
    JANUARY_TO_DECEMBER = 'january_to_december'
    APRIL_TO_MARCH = 'april_to_march'

    class Labels:
        JANUARY_TO_DECEMBER = _('January to december')
        APRIL_TO_MARCH = _('April to march')


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
        TYPE_1 = _('ind 50620 / 10/20%:n vaihtelut')
        TYPE_2 = _('ind 4661 / 10/20%:n vaihtelut')
        TYPE_3 = _('ind 418 / 10%:n vaihtelu')
        TYPE_4 = _('ind 418 / 20%:n vaihtelu')
        TYPE_5 = _('ind 392')
        TYPE_6 = _('ind 100 (pyöristys)')
        TYPE_7 = _('ind 100')


class DueDatesType(Enum):
    """
    In Finnish: Laskutusjako
    """
    CUSTOM = 'custom'
    FIXED = 'fixed'

    class Labels:
        CUSTOM = _('Custom')
        FIXED = _('Fixed')


class RentAdjustmentType(Enum):
    DISCOUNT = 'discount'
    INCREASE = 'increase'

    class Labels:
        DISCOUNT = _('Discount')
        INCREASE = _('Increase')


class RentAdjustmentAmountType(Enum):
    PERCENT_PER_YEAR = 'percent_per_year'
    PERCENT_TOTAL = 'percent_total'
    AMOUNT_PER_YEAR = 'amount_per_year'
    AMOUNT_TOTAL = 'amount_total'

    class Labels:
        PERCENT_PER_YEAR = _('% per year')
        PERCENT_TOTAL = _('% total')
        AMOUNT_PER_YEAR = _('€ per year')
        AMOUNT_TOTAL = _('€ total')


class InvoiceDeliveryMethod(Enum):
    MAIL = 'mail'
    ELECTRONIC = 'electronic'

    class Labels:
        MAIL = _('Mail')
        ELECTRONIC = _('Electronic')


class InvoiceState(Enum):
    OPEN = 'open'
    PAID = 'paid'
    REFUNDED = 'refunded'

    class Labels:
        OPEN = _('Open')
        PAID = _('Paid')
        REFUNDED = _('Refunded')


class InvoiceType(Enum):
    CHARGE = 'charge'
    CREDIT_NOTE = 'credit_note'

    class Labels:
        CHARGE = _('Charge')
        CREDIT_NOTE = _('Credit note')


class ContactType(Enum):
    PERSON = 'person'
    BUSINESS = 'business'
    UNIT = 'unit'
    ASSOCIATION = 'association'
    OTHER = 'other'

    class Labels:
        PERSON = _('Person')
        BUSINESS = _('Business')
        UNIT = _('Unit')
        ASSOCIATION = _('Association')
        OTHER = _('Other')
