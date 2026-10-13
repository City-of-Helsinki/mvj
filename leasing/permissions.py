from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS

from leasing.models.area_note import AreaNote
from leasing.models.basis_of_rent import (
    BasisOfRent,
    BasisOfRentBuildPermissionType,
    BasisOfRentDecision,
    BasisOfRentPlotType,
    BasisOfRentPropertyIdentifier,
    BasisOfRentRate,
)
from leasing.models.comment import Comment, CommentTopic
from leasing.models.contact import Contact
from leasing.models.contract import (
    Collateral,
    CollateralType,
    Contract,
    ContractChange,
    ContractType,
)
from leasing.models.debt_collection import (
    CollectionCourtDecision,
    CollectionLetter,
    CollectionLetterTemplate,
    CollectionNote,
    InterestRate,
)
from leasing.models.decision import (
    Condition,
    ConditionType,
    Decision,
    DecisionMaker,
    DecisionType,
)
from leasing.models.infill_development_compensation import (
    InfillDevelopmentCompensation,
    InfillDevelopmentCompensationAttachment,
    InfillDevelopmentCompensationDecision,
    InfillDevelopmentCompensationIntendedUse,
    InfillDevelopmentCompensationLease,
)
from leasing.models.inspection import Inspection, InspectionAttachment
from leasing.models.invoice import (
    Invoice,
    InvoiceNote,
    InvoicePayment,
    InvoiceRow,
    InvoiceSet,
)
from leasing.models.land_area import (
    ConstructabilityDescription,
    CustomDetailedPlan,
    LeaseArea,
    LeaseAreaAddress,
    LeaseAreaAttachment,
    PlanUnit,
    PlanUnitIntendedUse,
    PlanUnitState,
    PlanUnitType,
    Plot,
    PlotDivisionState,
    UsageDistribution,
)
from leasing.models.lease import (
    ApplicationMetadata,
    District,
    Financing,
    Hitas,
    IntendedUse,
    Lease,
    LeaseIdentifier,
    LeaseStateLog,
    LeaseType,
    Management,
    Municipality,
    NoticePeriod,
    Regulation,
    RelatedLease,
    ReservationProcedure,
    SpecialProject,
    StatisticalUse,
    SupportiveHousing,
)
from leasing.models.leasehold_transfer import (
    LeaseholdTransfer,
    LeaseholdTransferParty,
    LeaseholdTransferProperty,
)
from leasing.models.receivable_type import ReceivableType
from leasing.models.rent import (
    ContractRent,
    EqualizedRent,
    FixedInitialYearRent,
    Index,
    IndexAdjustedRent,
    LeaseBasisOfRent,
    LeaseBasisOfRentManagementSubvention,
    LeaseBasisOfRentTemporarySubvention,
    ManagementSubvention,
    ManagementSubventionFormOfManagement,
    OldDwellingsInHousingCompaniesPriceIndex,
    PayableRent,
    Rent,
    RentAdjustment,
    RentDueDate,
    RentIntendedUse,
    TemporarySubvention,
)
from leasing.models.report_storage import ReportStorage
from leasing.models.service_unit import ServiceUnit
from leasing.models.tenant import Tenant, TenantContact, TenantRentShare
from leasing.models.ui_data import UiData
from leasing.models.vat import Vat
from utils.group_permissions import UG, GroupModelPermissions

LEASING_GROUP_MODEL_PERMISSIONS: GroupModelPermissions = {
    AreaNote: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    DecisionMaker: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    DecisionType: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Decision: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "change"),
            UG.SOPIMUSVALMISTELIJA: ("view", "change"),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "change"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
            "conditions": {
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "change",
                UG.PERINTALAKIMIES: "change",
            },
        },
    },
    ConditionType: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Condition: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "change"),
            UG.SOPIMUSVALMISTELIJA: ("view", "change"),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "change"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "change",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
            "description": {UG.LASKUTTAJA: "change"},
            "id": {
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.PERINTALAKIMIES: "view",
            },
            "supervised_date": {UG.LASKUTTAJA: "change"},
            "supervision_date": {UG.LASKUTTAJA: "change"},
            "type": {
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.PERINTALAKIMIES: "view",
            },
        },
    },
    RentIntendedUse: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Rent: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "change"),
            UG.SOPIMUSVALMISTELIJA: ("view", "change"),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "change"),
            UG.LASKUTTAJA: ("view", "change"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
            "due_dates_type": {UG.LASKUTTAJA: "change"},
            "due_dates_per_year": {UG.LASKUTTAJA: "change"},
            "due_dates": {UG.LASKUTTAJA: "change"},
            "rent_adjustments": {
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "change",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
            },
            "override_receivable_type": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
            "old_dwellings_in_housing_companies_price_index": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
            "periodic_rent_adjustment_type": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    RentDueDate: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view", "add", "change", "delete"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "change",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    FixedInitialYearRent: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    ContractRent: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    IndexAdjustedRent: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    EqualizedRent: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view",),
        },
        "fields": {},
    },
    RentAdjustment: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "change",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
            "full_amount": {UG.VALMISTELIJA: "view"},
        },
    },
    ManagementSubvention: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    ManagementSubventionFormOfManagement: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    TemporarySubvention: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PayableRent: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Index: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    LeaseBasisOfRent: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
            "locked_at": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    LeaseBasisOfRentManagementSubvention: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    LeaseBasisOfRentTemporarySubvention: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    BasisOfRentPlotType: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    BasisOfRentBuildPermissionType: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    BasisOfRent: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    BasisOfRentRate: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    BasisOfRentPropertyIdentifier: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    BasisOfRentDecision: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    CommentTopic: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: None,
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "view",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    Comment: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view", "add", "change", "delete"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: None,
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "change",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    Contact: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: (
                "view",
                "add",
                "change",
                "view_contact_contacts_active_leases",
            ),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: (
                "view",
                "add",
                "change",
                "delete",
                "view_contact_contacts_active_leases",
            ),
            UG.PERINTALAKIMIES: (
                "view",
                "change",
                "view_contact_contacts_active_leases",
            ),
            UG.LASKUTTAJA: (
                "view",
                "add",
                "change",
                "delete",
                "view_contact_contacts_active_leases",
            ),
            UG.PAAKAYTTAJA: (
                "view",
                "add",
                "change",
                "delete",
                "view_contact_contacts_active_leases",
            ),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "change",
                UG.PAAKAYTTAJA: "change",
            },
            "national_identification_number": {
                UG.SELAILIJA: None,
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "change",
                UG.PAAKAYTTAJA: "change",
            },
            "phone": {UG.VALMISTELIJA: "change", UG.PERINTALAKIMIES: "change"},
            "email": {UG.VALMISTELIJA: "change", UG.PERINTALAKIMIES: "change"},
            "contacts_active_leases": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "view",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "view",
            },
        },
    },
    ContractType: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Contract: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "change"),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "change"),
            UG.LASKUTTAJA: ("view", "change"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "change",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
            "ktj_link": {UG.VALMISTELIJA: "change", UG.PERINTALAKIMIES: "change"},
            "collaterals": {UG.LASKUTTAJA: "change"},
            "signing_date": {UG.PERINTALAKIMIES: "change"},
            "executor": {UG.PERINTALAKIMIES: "change"},
            "contract_changes": {UG.PERINTALAKIMIES: "change"},
        },
    },
    Collateral: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view", "add", "change", "delete"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "change",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "change",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    CollateralType: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    ContractChange: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "change"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "change",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
            "executor": {UG.PERINTALAKIMIES: "change"},
        },
    },
    CollectionLetter: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: None,
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "view",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    CollectionLetterTemplate: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    CollectionNote: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view", "add", "change", "delete"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: None,
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "view",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "change",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    CollectionCourtDecision: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: None,
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "view",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    CustomDetailedPlan: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    InterestRate: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    LeaseType: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Municipality: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    District: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    IntendedUse: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    StatisticalUse: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    SupportiveHousing: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Financing: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Management: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Regulation: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Hitas: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    NoticePeriod: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    SpecialProject: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    ReservationProcedure: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    LeaseIdentifier: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Lease: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view", "change"),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view", "change"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete", "delete_nonempty"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
            "start_date": {UG.VALMISTELIJA: "view"},
            "end_date": {UG.VALMISTELIJA: "view"},
            "tenants": {
                UG.VALMISTELIJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "change",
            },
            "rents": {
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "change",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "change",
            },
            "decisions": {UG.SOPIMUSVALMISTELIJA: "change"},
            "contracts": {
                UG.SOPIMUSVALMISTELIJA: "change",
                UG.SYOTTAJA: "change",
                UG.LASKUTTAJA: "change",
            },
            "internal_order": {
                UG.VALMISTELIJA: "view",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "change",
            },
            "invoice_notes": {
                UG.VALMISTELIJA: "view",
                UG.SYOTTAJA: "view",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "change",
            },
            "invoicing_enabled_at": {
                UG.VALMISTELIJA: "view",
                UG.SYOTTAJA: "view",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "change",
            },
            "rent_info_completed_at": {
                UG.VALMISTELIJA: "view",
                UG.PERINTALAKIMIES: "view",
            },
            "target_statuses": {UG.VALMISTELIJA: "view", UG.SYOTTAJA: "view"},
            "area_searches": {UG.VALMISTELIJA: "view", UG.SYOTTAJA: "view"},
            "related_plot_applications": {
                UG.VALMISTELIJA: "view",
                UG.SYOTTAJA: "view",
            },
            "application_metadata": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    LeaseStateLog: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view",),
        },
        "fields": {},
    },
    RelatedLease: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    InfillDevelopmentCompensation: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    InfillDevelopmentCompensationLease: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    InfillDevelopmentCompensationDecision: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    InfillDevelopmentCompensationIntendedUse: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    InfillDevelopmentCompensationAttachment: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    Inspection: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    InspectionAttachment: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    ReceivableType: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    InvoiceSet: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view", "add", "change", "delete"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Invoice: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view", "add", "change", "delete"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: None,
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "view",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "change",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    InvoiceRow: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view", "add", "change", "delete"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: None,
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "view",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "change",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    InvoiceNote: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view", "add", "change", "delete"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: None,
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "view",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "change",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    InvoicePayment: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view", "add", "change", "delete"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: None,
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "view",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "change",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    LeaseArea: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
            "plots": {UG.PERINTALAKIMIES: "view"},
            "plan_units": {UG.PERINTALAKIMIES: "view"},
            "archived_at": {UG.VALMISTELIJA: "view", UG.PERINTALAKIMIES: "view"},
            "archived_note": {
                UG.VALMISTELIJA: "view",
                UG.PERINTALAKIMIES: "view",
            },
            "archived_decision": {
                UG.VALMISTELIJA: "view",
                UG.PERINTALAKIMIES: "view",
            },
        },
    },
    LeaseholdTransfer: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view", "delete"),
            UG.SYOTTAJA: ("view", "delete"),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "view",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "view",
            },
        },
    },
    LeaseholdTransferParty: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view", "delete"),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "view",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "view",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "view",
            },
            "national_identification_number": {
                UG.SELAILIJA: None,
                UG.VALMISTELIJA: None,
                UG.SOPIMUSVALMISTELIJA: None,
            },
        },
    },
    LeaseholdTransferProperty: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view", "delete"),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "delete"),
        },
        "fields": {},
    },
    LeaseAreaAddress: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    LeaseAreaAttachment: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    ConstructabilityDescription: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    Plot: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    UsageDistribution: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PlanUnitType: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PlotDivisionState: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PlanUnitState: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PlanUnitIntendedUse: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PlanUnit: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    ServiceUnit: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view",),
        },
        "fields": {},
    },
    Tenant: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view", "change"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
            "reference": {UG.LASKUTTAJA: "change"},
            "tenantcontact_set": {UG.LASKUTTAJA: "change"},
        },
    },
    TenantContact: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view", "add", "change"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "change",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    TenantRentShare: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view", "add", "change"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: "view",
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "view",
                UG.LASKUTTAJA: "change",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    Vat: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    OldDwellingsInHousingCompaniesPriceIndex: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    ApplicationMetadata: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    UiData: {
        "model": {
            UG.SELAILIJA: ("view", "add", "change", "delete"),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view", "add", "change", "delete"),
            UG.PAAKAYTTAJA: (
                "view",
                "add",
                "change",
                "delete",
                "edit_global_ui_data",
            ),
        },
        "fields": {},
    },
    # leasing.report_storage
    ReportStorage: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: None,
            UG.SOPIMUSVALMISTELIJA: None,
            UG.SYOTTAJA: None,
            UG.PERINTALAKIMIES: None,
            UG.LASKUTTAJA: None,
            UG.PAAKAYTTAJA: ("view", "delete"),
        },
        "fields": {},
    },
}


class MvjDjangoModelPermissions(permissions.DjangoModelPermissions):
    """Customized Django REST Framework DjangoModelPermissions
    class that includes checking for the "view" permissions too.
    """

    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": [],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }


class MvjDjangoModelPermissionsOrAnonReadOnly(
    permissions.DjangoModelPermissionsOrAnonReadOnly
):
    """Customized Django REST Framework DjangoModelPermissions
    class that includes checking for the "view" permissions too.
    """

    perms_map = {
        "GET": [],
        "OPTIONS": [],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }


class PerMethodPermission(permissions.BasePermission):
    """Per method permission check

    Permission where the required permissions can be configured
    per method. Returns True if no permissions are configured.
    If multiple permissions listed, the user must have all of
    the permissions."""

    perms_map = {
        "GET": [],
        "POST": [],
        "PUT": [],
        "PATCH": [],
        "DELETE": [],
        "OPTIONS": [],
    }

    def get_required_permissions(self, method, view):
        """Get required permissions for method and view combo

        Given method and view, return the list of permission
        codes that the user is required to have.
        """
        perms_map = self.perms_map.copy()

        if hasattr(view, "perms_map"):
            perms_map.update(view.perms_map)

        if method not in perms_map:
            return []

        return perms_map[method]

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        required_perms = self.get_required_permissions(request.method, view)

        return request.user.has_perms(required_perms)


class IsSameUser(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not hasattr(obj, "user") or not obj.user:
            return True

        return obj.user == request.user


class IsMemberOfSameServiceUnit(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Users can read data from other service units
        if request.method in SAFE_METHODS or not hasattr(obj, "get_service_unit"):
            return True

        if request.user.is_superuser:
            return True

        service_unit = obj.get_service_unit()

        if service_unit in request.user.service_units.all():
            return True

        return False
