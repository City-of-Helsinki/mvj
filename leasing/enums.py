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


class RentType(Enum):
    FIXED = 'fixed'
    INDEX = 'index'
    ONE_TIME = 'one_time'
    FREE = 'free'
    MANUAL = 'manual'

    class Labels:
        FIXED = _('Fixed sum')
        INDEX = _('Index-linked')
        ONE_TIME = _('One time')
        FREE = _('Free')
        MANUAL = _('Manual')


LEASE_IDENTIFIER_TYPE = (
    ('A1', 'Asuntotontit'),
    ('A2', 'Opiskelija-asuntotontit'),
    ('A3', 'Vanhusten asunto- ja vanhainkotitontit'),
    ('A4', 'Asuntotontteihin liittyvä pysäköintit.'),
    ('S0', 'Sekalaiset vuokraukset'),
    ('T1', 'Teollisuus- ja varastotontit'),
    ('O1', 'Käyttöoikeudet'),
    ('T2', 'Teollis./varastot. liittyv. pysäköintit.'),
    ('H1', 'Huoltoasema'),
    ('H2', 'Jakeluasema'),
    ('L1', 'Liike- ja toimistotontit'),
    ('L2', 'Yleisen rakennuksen tontit'),
    ('L3', 'Liike/Yleistenr. tonttien pysäköintit.'),
    ('O2', 'Laiturinpito ja poijuluvat'),
    ('O3', 'Kokoontumisluvat'),
    ('O4', 'Muut luvat'),
    ('K0', 'Kaupungin sisäiset (tilapäiset vuokr.)'),
    ('V5', 'Helsingin Satama'),
    ('V2', 'Helsingin Energia'),
    ('V6', 'Helsingin Vesi'),
    ('V4', 'Liikennelaitos'),
    ('V1', 'Elintarviketukkukaupan keskus'),
    ('V3', 'Keskuspesula'),
    ('Y3', 'Liikuntavirasto'),
    ('Y5', 'Rakennusvirasto'),
    ('Y6', 'Sosiaalivirasto'),
    ('Y7', 'Terveysvirasto'),
    ('Y2', 'Opetusvirasto'),
    ('Y4', 'Pelastuslaitos'),
    ('Y1', 'Korkeasaari'),
    ('Y8', 'Nuorisoasiainkeskus'),
    ('TY', 'TYHJÄ TONTTI'),
    ('MA', 'Maapoliittinen sopimus'),
    ('Y9', 'Kiinteistövirasto tilakeskus'),
    ('MY', 'Myynti/maksamaton kauppahinta'),
    ('R0', 'SIIRTOLAPUUTARHA ei käytössä'),
    ('VS', 'Väestönsuojakorvaukset'),
    ('Y0', 'Varhaiskasvatusvirasto'),
    ('T3', 'Teollisuus- ja varatotontit (alv:set)'),
    ('S1', 'Liikuntaviraston ulosvuokraus'),
)

LEASE_IDENTIFIER_MUNICIPALITY = (
    ('2', 'ESPOO'),
    ('8', 'HANKO'),
    ('1', 'HELSINKI'),
    ('3', 'INKOO'),
    ('4', 'KIRKKONUMMI'),
    ('9', 'LOHJA'),
    ('0', 'MUU'),
    ('7', 'SIPOO'),
    ('6', 'VANTAA'),
    ('5', 'VIHTI'),
)

LEASE_IDENTIFIER_DISTRICT = (
    ('01', 'KRUUNUNHAKA'),
    ('02', 'KLUUVI'),
    ('03', 'KAARTINKAUPUNKI'),
    ('04', 'KAMPPI'),
    ('05', 'PUNAVUORI'),
    ('06', 'EIRA'),
    ('07', 'ULLANLINNA'),
    ('08', 'KATAJANOKKA'),
    ('09', 'KAIVOPUISTO'),
    ('10', 'SÖRNÄINEN'),
    ('11', 'KALLIO'),
    ('12', 'ALPPIHARJU'),
    ('13', 'ETU-TÖÖLÖ'),
    ('14', 'TAKA-TÖÖLÖ'),
    ('15', 'MEILAHTI'),
    ('16', 'RUSKEASUO'),
    ('17', 'PASILA'),
    ('18', 'LAAKSO'),
    ('19', 'MUSTIKKAMAA-KORKEAS'),
    ('20', 'LÄNSISATAMA'),
    ('21', 'HERMANNI'),
    ('22', 'VALLILA'),
    ('23', 'TOUKOLA'),
    ('24', 'KUMPULA'),
    ('25', 'KÄPYLÄ'),
    ('26', 'KOSKELA'),
    ('27', 'VANHAKAUPUNKI'),
    ('28', 'OULUNKYLÄ'),
    ('29', 'HAAGA'),
    ('30', 'MUNKKINIEMI'),
    ('31', 'LAUTTASAARI'),
    ('32', 'KONALA'),
    ('33', 'KAARELA'),
    ('34', 'PAKILA'),
    ('35', 'TUOMARINKYLÄ'),
    ('36', 'VIIKKI'),
    ('37', 'PUKINMÄKI'),
    ('38', 'MALMI'),
    ('39', 'TAPANINKYLÄ'),
    ('40', 'SUUTARILA'),
    ('41', 'SUURMETSÄ'),
    ('42', 'KULOSAARI'),
    ('43', 'HERTTONIEMI'),
    ('44', 'TAMMISALO'),
    ('45', 'VARTIOKYLÄ'),
    ('46', 'PITÄJÄNMÄKI'),
    ('47', 'MELLUNKYLÄ'),
    ('48', 'VARTIOSAARI'),
    ('49', 'LAAJASALO'),
    ('50', 'VILLINKI'),
    ('51', 'SANTAHAMINA'),
    ('52', 'SUOMENLINNA'),
    ('53', 'ULKOSAARET'),
    ('54', 'VUOSAARI'),
    ('26', 'MANKKAA'),
    ('10', 'OTANIEMI'),
    ('12', 'TAPIOLA'),
    ('16', 'POHJOIS-TAPIOLA'),
    ('17', 'LAAJALAHTI'),
    ('51', 'LEPPÄVAARA'),
    ('54', 'KILO'),
    ('00', 'MUU'),
    ('31', 'KAITAA'),
    ('71', 'ILOLA'),
    ('73', 'REKOLA'),
    ('83', 'METSOLA'),
    ('98', 'SOTUNKI'),
    ('89', 'LAKISTO'),
    ('83', 'BODOM'),
    ('40', 'ESPOON KESKUS'),
    ('34', 'ESPOONLAHTI'),
    ('87', 'LAHNUS'),
    ('88', 'VELSKOLA'),
    ('78', 'NUUKSIO'),
    ('76', 'SIIKAJÄRVI'),
    ('86', 'LUUKKI'),
    ('84', 'RÖYLÄ'),
    ('56', 'SALMENKALLIO'),
    ('57', 'TALOSAARI'),
    ('58', 'KARHUSAARI'),
    ('59', 'ULTUNA'),
    ('55', 'ÖSTERSUNDOM'),
    ('93', 'VAARALA'),
    ('91', 'LÄNSIMÄKI'),
    ('95', 'RAJAKYLÄ'),
    ('92', 'OJANKO'),
)
