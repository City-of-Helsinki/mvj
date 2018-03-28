from django.utils.translation import ugettext_lazy as _
from enumfields import Enum


class Classification(Enum):
    PUBLIC = 'public'
    CONFIDENTIAL = 'confidential'
    OFFICIAL = 'official'

    class Labels:
        PUBLIC = _('Public')
        CONFIDENTIAL = _('Confidential')
        OFFICIAL = _('Official')


class LeaseState(Enum):
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
    TRANSFER = 'transfer'

    class Labels:
        TRANSFER = _('Transfer')


class PeriodType(Enum):
    NO_PERIOD = 'no_period'
    TIME_PERIOD = 'time_period'
    OTHER = 'other'

    class Labels:
        NO_PERIOD = _('No period')
        TIME_PERIOD = _('Time period')
        OTHER = _('Other')


class TenantContactType(Enum):
    TENANT = 'tenant'
    BILLING = 'billing'
    CONTACT = 'contact'

    class Labels:
        TENANT = _("Tenant")
        BILLING = _("Billing contact")
        CONTACT = _("Contact")


class LocationType(Enum):
    SURFACE = 'surface'
    UNDERGROUND = 'underground'

    class Labels:
        SURFACE = _('Surface')
        UNDERGROUND = _('Underground')


class LeaseAreaType(Enum):
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
    REAL_PROPERTY = 'real_property'
    UNSEPARATED_PARCEL = 'unseparated_parcel'

    class Labels:
        REAL_PROPERTY = _('Real property')
        UNSEPARATED_PARCEL = _('Unseparated parcel')


class RentRatePeriod(Enum):
    PER_MONTH = 'per_month'
    PER_YEAR = 'per_year'

    class Labels:
        PER_MONTH = _('/ month')
        PER_YEAR = _('/ year')


class ConstructabilityState(Enum):
    UNVERIFIED = 'unverified'
    REQUIRES_MEASURES = 'requires_measures'
    COMPLETE = 'complete'

    class Labels:
        UNVERIFIED = _('Unverified')
        REQUIRES_MEASURES = _('Requires measures')
        COMPLETE = _('Complete')


class ConstructabilityType(Enum):
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
    ASKED = 'asked'
    READY = 'ready'

    class Labels:
        ASKED = _('Asked')
        READY = _('Ready')


class ConstructabilityReportInvestigationState(Enum):
    NO_NEED = 'no_need'
    ONGOING = 'ongoing'
    READY = 'ready'

    class Labels:
        NO_NEED = _('No need')
        ONGOING = _('Ongoing')
        READY = _('Ready')
