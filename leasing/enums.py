from django.utils.translation import ugettext_lazy as _
from enumfields import Enum


class ApplicationState(Enum):
    UNHANDLED = 'unhandled'
    HANDLED = 'handled'
    ARCHIVED = 'archived'
    FINISHED = 'finished'

    class Labels:
        UNHANDLED = _('Unhandled')
        HANDLED = _('Handled')
        ARCHIVED = _('Archived')
        FINISHED = _('Finished')


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


class LeaseState(Enum):
    DRAFT = 'draft'
    ARCHIVED = 'archived'
    SENT = 'sent'
    APPROVED = 'approved'

    class Labels:
        DRAFT = _('Draft')
        ARCHIVED = _('Archived')
        SENT = _('Sent')
        APPROVED = _('Approved')


class LeaseConditionType(Enum):
    SPECIAL_CONDITION = 'special_condition'
    HITAS = 'hitas'
    ASO = 'aso'
    KALASATAMA = 'kalasatama'
    OTHER = 'other'

    class Labels:
        SPECIAL_CONDITION = _('Special condition')
        HITAS = _('Hitas')
        ASO = _('ASO')
        KALASATAMA = _('Kalasatama')
        OTHER = _('Other')


class DecisionType(Enum):
    RENT_REVIEW = 'rent_review'
    TERM_CHANGE = 'term_change'
    CONTRACT_CHANGE = 'contract_change'
    CONSTRUCTION_DRAFT_REVIEW = 'construction_draft_overview'
    OTHER = 'other'

    class Labels:
        RENT_REVIEW = _('Rent review')
        TERM_CHANGE = _('Term change')
        CONTRACT_CHANGE = _('Contract change')
        CONSTRUCTION_DRAFT_REVIEW = _('Construction Draft Overview')
        OTHER = _('Other')
