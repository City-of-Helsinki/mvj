from landuse.models.agreement import (
    AgreementAddress,
    AgreementPreparer,
    AuthorizedSignatory,
    DetailedPlan,
    District,
    LandUseAgreement,
)
from landuse.models.compensation import LandPolicyProgram, LandUseCompensation
from landuse.models.contract import (
    CashDepositCollateral,
    Contract,
    ContractChange,
    DepositPledgeCollateral,
    MortgageDeedCollateral,
    MortgageDeedPropertyIdentifier,
    OtherCollateral,
    PersonalGuaranteeCollateral,
)
from landuse.models.decision import Decision, DecisionCondition
from landuse.models.invoice import (
    Invoice,
    InvoiceItem,
    InvoiceRecipientSnapshot,
    ShadowSalesLedgerEntry,
)
from landuse.models.party import (
    AgreementParty,
    BillingDetails,
    ContactPerson,
    InvoiceRecipient,
)
from landuse.models.payment_schedule import (
    PaymentSchedule,
    PaymentScheduleInstallment,
    PaymentScheduleInstallmentItem,
)
from landuse.models.site import (
    AgreementSite,
    DetailedPlanSite,
    SiteIntendedUse,
    SiteTenureType,
)
from utils.group_permissions import UG, GroupModelPermissions

LANDUSE_GROUP_MODEL_PERMISSIONS: GroupModelPermissions = {
    AgreementAddress: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change"),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    AgreementParty: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view", "change"),
            UG.LASKUTTAJA: ("view", "change"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    AgreementPreparer: {
        "model": {
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view",),
        },
        "fields": {},
    },
    AgreementSite: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    AuthorizedSignatory: {
        "model": {
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    BillingDetails: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: (
                "view",
                "change",
            ),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    CashDepositCollateral: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    ContactPerson: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: (
                "view",
                "change",
            ),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Contract: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    ContractChange: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Decision: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    DecisionCondition: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    DepositPledgeCollateral: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    DetailedPlan: {
        "model": {
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view",),
        },
        "fields": {},
    },
    DetailedPlanSite: {
        "model": {
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view",),
        },
        "fields": {},
    },
    District: {
        "model": {
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Invoice: {
        "model": {
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view", "add", "change", "delete"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    InvoiceItem: {
        "model": {
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view", "add", "change", "delete"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    InvoiceRecipient: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view", "add", "change", "delete"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    InvoiceRecipientSnapshot: {
        "model": {
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    LandPolicyProgram: {
        "model": {
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    LandUseAgreement: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change"),
            UG.SOPIMUSVALMISTELIJA: ("view", "change"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    LandUseCompensation: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    MortgageDeedCollateral: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    MortgageDeedPropertyIdentifier: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    OtherCollateral: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PaymentSchedule: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view", "change"),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PaymentScheduleInstallment: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PaymentScheduleInstallmentItem: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PersonalGuaranteeCollateral: {
        "model": {
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    ShadowSalesLedgerEntry: {
        "model": {
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view",),
        },
        "fields": {},
    },
    SiteIntendedUse: {
        "model": {
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    SiteTenureType: {
        "model": {
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
}
