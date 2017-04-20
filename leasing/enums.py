from django.utils.translation import ugettext_lazy as _
from enumfields import Enum


class ApplicationType(Enum):
    REAL_PROPERTY_UNIT = 'real_property_unit'
    DETACHED_HOUSE = 'detached_house'
    OTHER = 'other'

    class Labels:
        REAL_PROPERTY_UNIT = _('Real property unit')
        DETACHED_HOUSE = _('Detached house')
        OTHER = _('Other')


class ShortTermReason(Enum):
    EARTHWORKS = 'earthworks'
    BUILDING_PERMIT = 'building_permit'

    class Labels:
        EARTHWORKS = _('For starting the earthworks')
        BUILDING_PERMIT = _('For applying for a building permit')
