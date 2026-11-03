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
from utils.enums import AuthGroupId as AG
from utils.group_permissions import GroupModelPermissions

LEASING_GROUP_MODEL_PERMISSIONS: GroupModelPermissions = {
    AreaNote: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    DecisionMaker: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    DecisionType: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Decision: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "change"),
            AG.SOPIMUSVALMISTELIJA: ("view", "change"),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "change"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
            "conditions": {
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "change",
                AG.PERINTALAKIMIES: "change",
            },
        },
    },
    ConditionType: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Condition: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "change"),
            AG.SOPIMUSVALMISTELIJA: ("view", "change"),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "change"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "change",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
            "description": {AG.LASKUTTAJA: "change"},
            "id": {
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.PERINTALAKIMIES: "view",
            },
            "supervised_date": {AG.LASKUTTAJA: "change"},
            "supervision_date": {AG.LASKUTTAJA: "change"},
            "type": {
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.PERINTALAKIMIES: "view",
            },
        },
    },
    RentIntendedUse: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Rent: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "change"),
            AG.SOPIMUSVALMISTELIJA: ("view", "change"),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "change"),
            AG.LASKUTTAJA: ("view", "change"),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
            "due_dates_type": {AG.LASKUTTAJA: "change"},
            "due_dates_per_year": {AG.LASKUTTAJA: "change"},
            "due_dates": {AG.LASKUTTAJA: "change"},
            "rent_adjustments": {
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "change",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
            },
            "override_receivable_type": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
            "old_dwellings_in_housing_companies_price_index": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
            "periodic_rent_adjustment_type": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    RentDueDate: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view", "add", "change", "delete"),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "change",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    FixedInitialYearRent: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    ContractRent: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    IndexAdjustedRent: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    EqualizedRent: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view",),
        },
        "fields": {},
    },
    RentAdjustment: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "change",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
            "full_amount": {AG.VALMISTELIJA: "view"},
        },
    },
    ManagementSubvention: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    ManagementSubventionFormOfManagement: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    TemporarySubvention: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PayableRent: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Index: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    LeaseBasisOfRent: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
            "locked_at": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    LeaseBasisOfRentManagementSubvention: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    LeaseBasisOfRentTemporarySubvention: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    BasisOfRentPlotType: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    BasisOfRentBuildPermissionType: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    BasisOfRent: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    BasisOfRentRate: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    BasisOfRentPropertyIdentifier: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    BasisOfRentDecision: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    CommentTopic: {
        "model": {
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: None,
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "view",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    Comment: {
        "model": {
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view", "add", "change", "delete"),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: None,
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "change",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    Contact: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: (
                "view",
                "add",
                "change",
                "view_contact_contacts_active_leases",
            ),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: (
                "view",
                "add",
                "change",
                "delete",
                "view_contact_contacts_active_leases",
            ),
            AG.PERINTALAKIMIES: (
                "view",
                "change",
                "view_contact_contacts_active_leases",
            ),
            AG.LASKUTTAJA: (
                "view",
                "add",
                "change",
                "delete",
                "view_contact_contacts_active_leases",
            ),
            AG.PAAKAYTTAJA: (
                "view",
                "add",
                "change",
                "delete",
                "view_contact_contacts_active_leases",
            ),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "change",
                AG.PAAKAYTTAJA: "change",
            },
            "national_identification_number": {
                AG.SELAILIJA: None,
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "change",
                AG.PAAKAYTTAJA: "change",
            },
            "phone": {AG.VALMISTELIJA: "change", AG.PERINTALAKIMIES: "change"},
            "email": {AG.VALMISTELIJA: "change", AG.PERINTALAKIMIES: "change"},
            "contacts_active_leases": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "view",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "view",
            },
        },
    },
    ContractType: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Contract: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "change"),
            AG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "change"),
            AG.LASKUTTAJA: ("view", "change"),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "change",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
            "ktj_link": {AG.VALMISTELIJA: "change", AG.PERINTALAKIMIES: "change"},
            "collaterals": {AG.LASKUTTAJA: "change"},
            "signing_date": {AG.PERINTALAKIMIES: "change"},
            "executor": {AG.PERINTALAKIMIES: "change"},
            "contract_changes": {AG.PERINTALAKIMIES: "change"},
        },
    },
    Collateral: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view", "add", "change", "delete"),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "change",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "change",
                AG.PAAKAYTTAJA: "change",
            },
            "pledgor_national_identification_number": {
                AG.SELAILIJA: None,
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "change",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "change",
                AG.PAAKAYTTAJA: "change",
            },
            "contract_party_national_identification_number": {
                AG.SELAILIJA: None,
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "change",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "change",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    ContractChange: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "change"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "change",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
            "executor": {AG.PERINTALAKIMIES: "change"},
        },
    },
    CollectionLetter: {
        "model": {
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: None,
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "view",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    CollectionLetterTemplate: {
        "model": {
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    CollectionNote: {
        "model": {
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view", "add", "change", "delete"),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: None,
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "view",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "change",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    CollectionCourtDecision: {
        "model": {
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: None,
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "view",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    CustomDetailedPlan: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    InterestRate: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    LeaseType: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Municipality: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    District: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    IntendedUse: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    StatisticalUse: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    SupportiveHousing: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Financing: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Management: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Regulation: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Hitas: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    NoticePeriod: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    SpecialProject: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    ReservationProcedure: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    LeaseIdentifier: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Lease: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view", "change"),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view", "change"),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete", "delete_nonempty"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
            "start_date": {AG.VALMISTELIJA: "view"},
            "end_date": {AG.VALMISTELIJA: "view"},
            "tenants": {
                AG.VALMISTELIJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "change",
            },
            "rents": {
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "change",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "change",
            },
            "decisions": {AG.SOPIMUSVALMISTELIJA: "change"},
            "contracts": {
                AG.SOPIMUSVALMISTELIJA: "change",
                AG.SYOTTAJA: "change",
                AG.LASKUTTAJA: "change",
            },
            "internal_order": {
                AG.VALMISTELIJA: "view",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "change",
            },
            "invoice_notes": {
                AG.VALMISTELIJA: "view",
                AG.SYOTTAJA: "view",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "change",
            },
            "invoicing_enabled_at": {
                AG.VALMISTELIJA: "view",
                AG.SYOTTAJA: "view",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "change",
            },
            "rent_info_completed_at": {
                AG.VALMISTELIJA: "view",
                AG.PERINTALAKIMIES: "view",
            },
            "target_statuses": {AG.VALMISTELIJA: "view", AG.SYOTTAJA: "view"},
            "area_searches": {AG.VALMISTELIJA: "view", AG.SYOTTAJA: "view"},
            "related_plot_applications": {
                AG.VALMISTELIJA: "view",
                AG.SYOTTAJA: "view",
            },
            "application_metadata": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    LeaseStateLog: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view",),
        },
        "fields": {},
    },
    RelatedLease: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    InfillDevelopmentCompensation: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    InfillDevelopmentCompensationLease: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    InfillDevelopmentCompensationDecision: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    InfillDevelopmentCompensationIntendedUse: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    InfillDevelopmentCompensationAttachment: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    Inspection: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    InspectionAttachment: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    ReceivableType: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    InvoiceSet: {
        "model": {
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view", "add", "change", "delete"),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Invoice: {
        "model": {
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view", "add", "change", "delete"),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: None,
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "view",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "change",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    InvoiceRow: {
        "model": {
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view", "add", "change", "delete"),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: None,
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "view",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "change",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    InvoiceNote: {
        "model": {
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view", "add", "change", "delete"),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: None,
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "view",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "change",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    InvoicePayment: {
        "model": {
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view", "add", "change", "delete"),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: None,
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "view",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "change",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    LeaseArea: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
            "plots": {AG.PERINTALAKIMIES: "view"},
            "plan_units": {AG.PERINTALAKIMIES: "view"},
            "archived_at": {AG.VALMISTELIJA: "view", AG.PERINTALAKIMIES: "view"},
            "archived_note": {
                AG.VALMISTELIJA: "view",
                AG.PERINTALAKIMIES: "view",
            },
            "archived_decision": {
                AG.VALMISTELIJA: "view",
                AG.PERINTALAKIMIES: "view",
            },
        },
    },
    LeaseholdTransfer: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view", "delete"),
            AG.SYOTTAJA: ("view", "delete"),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "view",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "view",
            },
        },
    },
    LeaseholdTransferParty: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view", "delete"),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "view",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "view",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "view",
            },
            "national_identification_number": {
                AG.SELAILIJA: None,
                AG.VALMISTELIJA: None,
                AG.SOPIMUSVALMISTELIJA: None,
            },
        },
    },
    LeaseholdTransferProperty: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view", "delete"),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "delete"),
        },
        "fields": {},
    },
    LeaseAreaAddress: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    LeaseAreaAttachment: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    ConstructabilityDescription: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    Plot: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    UsageDistribution: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PlanUnitType: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PlotDivisionState: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PlanUnitState: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PlanUnitIntendedUse: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PlanUnit: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    ServiceUnit: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view",),
        },
        "fields": {},
    },
    Tenant: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view", "change"),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
            "reference": {AG.LASKUTTAJA: "change"},
            "tenantcontact_set": {AG.LASKUTTAJA: "change"},
        },
    },
    TenantContact: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view", "add", "change"),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "change",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    TenantRentShare: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view", "add", "change"),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: "view",
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "view",
                AG.LASKUTTAJA: "change",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    Vat: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    OldDwellingsInHousingCompaniesPriceIndex: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    ApplicationMetadata: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    UiData: {
        "model": {
            AG.SELAILIJA: ("view", "add", "change", "delete"),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view", "add", "change", "delete"),
            AG.PAAKAYTTAJA: (
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
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: None,
            AG.SOPIMUSVALMISTELIJA: None,
            AG.SYOTTAJA: None,
            AG.PERINTALAKIMIES: None,
            AG.LASKUTTAJA: None,
            AG.PAAKAYTTAJA: ("view", "delete"),
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
