from collections import defaultdict
from collections.abc import Mapping
from enum import IntEnum

from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError


class UserGroup(IntEnum):
    SELAILIJA = 1
    VALMISTELIJA = 2
    SOPIMUSVALMISTELIJA = 3
    SYOTTAJA = 4
    PERINTALAKIMIES = 5
    LASKUTTAJA = 6
    PAAKAYTTAJA = 7


UG = UserGroup


DEFAULT_FIELD_PERMS = {
    "areanote": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "areasearch": {
        UG.SELAILIJA: None,
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "decision": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "condition": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "change",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "rent": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "rentduedate": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "change",
        UG.PAAKAYTTAJA: "change",
    },
    "fixedinitialyearrent": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "contractrent": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "rentadjustment": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "change",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "leasebasisofrent": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "basisofrent": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "basisofrentrate": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "basisofrentdecision": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "comment": {
        UG.SELAILIJA: None,
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "change",
        UG.PAAKAYTTAJA: "change",
    },
    "commenttopic": {
        UG.SELAILIJA: None,
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "view",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "contact": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "change",
        UG.PAAKAYTTAJA: "change",
    },
    "contract": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "change",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "contractchange": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "change",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "collateral": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "change",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "change",
        UG.PAAKAYTTAJA: "change",
    },
    "collectionletter": {
        UG.SELAILIJA: None,
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "view",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "collectionnote": {
        UG.SELAILIJA: None,
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "view",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "change",
        UG.PAAKAYTTAJA: "change",
    },
    "collectioncourtdecision": {
        UG.SELAILIJA: None,
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "view",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "customdetailedplan": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "lease": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "infilldevelopmentcompensation": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "infilldevelopmentcompensationlease": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "infilldevelopmentcompensationdecision": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "infilldevelopmentcompensationintendeduse": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "infilldevelopmentcompensationattachment": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "inspection": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "inspectionattachment": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "invoice": {
        UG.SELAILIJA: None,
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "view",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "change",
        UG.PAAKAYTTAJA: "change",
    },
    "invoicerow": {
        UG.SELAILIJA: None,
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "view",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "change",
        UG.PAAKAYTTAJA: "change",
    },
    "invoicenote": {
        UG.SELAILIJA: None,
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "view",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "change",
        UG.PAAKAYTTAJA: "change",
    },
    "invoicepayment": {
        UG.SELAILIJA: None,
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "view",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "change",
        UG.PAAKAYTTAJA: "change",
    },
    "leasearea": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "leaseareaaddress": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "leaseareaattachment": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "leaseholdtransfer": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "view",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "view",
    },
    "leaseholdtransferparty": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "view",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "view",
    },
    "constructabilitydescription": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "plot": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "plotsearch": {
        UG.SELAILIJA: None,
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "plotsearchsubtype": {
        UG.SELAILIJA: None,
        UG.VALMISTELIJA: "change",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "change",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "planunit": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "tenant": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "view",
        UG.PAAKAYTTAJA: "change",
    },
    "tenantcontact": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "change",
        UG.PAAKAYTTAJA: "change",
    },
    "tenantrentshare": {
        UG.SELAILIJA: "view",
        UG.VALMISTELIJA: "view",
        UG.SOPIMUSVALMISTELIJA: "view",
        UG.SYOTTAJA: "change",
        UG.PERINTALAKIMIES: "view",
        UG.LASKUTTAJA: "change",
        UG.PAAKAYTTAJA: "change",
    },
}

CUSTOM_FIELD_PERMS = {
    "lease": {
        "start_date": {UG.VALMISTELIJA: "view"},
        "end_date": {UG.VALMISTELIJA: "view"},
        "tenants": {
            UG.VALMISTELIJA: "view",
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
        "rent_info_completed_at": {UG.VALMISTELIJA: "view", UG.PERINTALAKIMIES: "view"},
        "target_statuses": {UG.VALMISTELIJA: "view", UG.SYOTTAJA: "view"},
        "area_searches": {UG.VALMISTELIJA: "view", UG.SYOTTAJA: "view"},
        "related_plot_applications": {UG.VALMISTELIJA: "view", UG.SYOTTAJA: "view"},
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
    "contact": {
        "national_identification_number": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: None,
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
    "condition": {
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
    "contract": {
        "ktj_link": {UG.VALMISTELIJA: "change", UG.PERINTALAKIMIES: "change"},
        "collaterals": {UG.LASKUTTAJA: "change"},
        "signing_date": {UG.PERINTALAKIMIES: "change"},
        "executor": {UG.PERINTALAKIMIES: "change"},
        "contract_changes": {UG.PERINTALAKIMIES: "change"},
    },
    "contractchange": {
        "executor": {UG.PERINTALAKIMIES: "change"},
    },
    "decision": {
        "conditions": {
            UG.VALMISTELIJA: "change",
            UG.SOPIMUSVALMISTELIJA: "change",
            UG.PERINTALAKIMIES: "change",
        }
    },
    "rent": {
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
    "rentadjustment": {"full_amount": {UG.VALMISTELIJA: "view"}},
    "tenant": {
        "reference": {UG.LASKUTTAJA: "change"},
        "tenantcontact_set": {UG.LASKUTTAJA: "change"},
    },
    "leasearea": {
        "plots": {UG.VALMISTELIJA: "view", UG.PERINTALAKIMIES: "view"},
        "plan_units": {UG.VALMISTELIJA: "view", UG.PERINTALAKIMIES: "view"},
        "archived_at": {UG.VALMISTELIJA: "view", UG.PERINTALAKIMIES: "view"},
        "archived_note": {UG.VALMISTELIJA: "view", UG.PERINTALAKIMIES: "view"},
        "archived_decision": {UG.VALMISTELIJA: "view", UG.PERINTALAKIMIES: "view"},
    },
    "leaseholdtransferparty": {
        "national_identification_number": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: None,
            UG.SOPIMUSVALMISTELIJA: None,
        }
    },
    "leasebasisofrent": {
        "locked_at": {
            UG.SELAILIJA: "view",
            UG.VALMISTELIJA: "view",
            UG.SOPIMUSVALMISTELIJA: "view",
            UG.SYOTTAJA: "change",
            UG.PERINTALAKIMIES: "view",
            UG.LASKUTTAJA: "view",
            UG.PAAKAYTTAJA: "change",
        }
    },
    "landuseagreement": {
        "landuseagreementlitigant": {
            UG.SELAILIJA: "view",
            UG.VALMISTELIJA: "view",
            UG.SOPIMUSVALMISTELIJA: "view",
            UG.SYOTTAJA: "change",
            UG.PERINTALAKIMIES: "view",
            UG.LASKUTTAJA: "change",
            UG.PAAKAYTTAJA: "change",
        },
        "landuseagreementaddress": {
            UG.SELAILIJA: "change",
            UG.VALMISTELIJA: "change",
            UG.SOPIMUSVALMISTELIJA: "change",
            UG.SYOTTAJA: "change",
            UG.PERINTALAKIMIES: "change",
            UG.LASKUTTAJA: "change",
            UG.PAAKAYTTAJA: "change",
        },
        "landuseagreementdecision": {
            UG.SELAILIJA: "view",
            UG.VALMISTELIJA: "view",
            UG.SOPIMUSVALMISTELIJA: "view",
            UG.SYOTTAJA: "change",
            UG.PERINTALAKIMIES: "view",
            UG.LASKUTTAJA: "view",
            UG.PAAKAYTTAJA: "change",
        },
    },
    "landuseagreementlitigant": {
        "landuseagreementlitigantcontact": {
            UG.SELAILIJA: "view",
            UG.VALMISTELIJA: "view",
            UG.SOPIMUSVALMISTELIJA: "view",
            UG.SYOTTAJA: "change",
            UG.PERINTALAKIMIES: "view",
            UG.LASKUTTAJA: "change",
            UG.PAAKAYTTAJA: "change",
        },
    },
}


def update(d, u):
    for k, v in u.items():
        if isinstance(v, Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v

    return d


class Command(BaseCommand):
    help = "Sets predefined field permissions for the predefined MVJ groups"

    def handle(self, *args, **options):  # NOQA
        if not apps.is_installed("field_permissions"):
            raise CommandError(
                'App "field_permissions" must be installed to use this command.'
            )

        from field_permissions.registry import field_permissions

        groups = {group.id: group for group in Group.objects.all()}
        permissions = {perm.codename: perm for perm in Permission.objects.all()}

        group_permissions = []
        all_field_permissions = []

        for model in field_permissions.get_models():
            model_name = model._meta.model_name

            # Find all the fields that the field permissions registry knows about
            perms = field_permissions.get_field_permissions_for_model(model)

            field_perms = {}
            for codename, name in sorted(perms):
                try:
                    all_field_permissions.append(permissions[codename])
                except KeyError:
                    raise CommandError(
                        '"{}" field permission is missing. Please run migrate to create '
                        "the missing permissions.".format(codename)
                    )

                if codename.startswith("change_"):
                    continue

                field_name = codename.replace("view_{}_".format(model_name), "")

                # Set field permissions to their default value
                if model_name in DEFAULT_FIELD_PERMS:
                    field_perms[field_name] = dict(DEFAULT_FIELD_PERMS[model_name])

            # Customize field permissions for this model
            if model_name in CUSTOM_FIELD_PERMS:
                update(field_perms, CUSTOM_FIELD_PERMS[model_name])

            # Generate Group permissions for all of the fields and groups
            for field_name, group_perms in field_perms.items():
                for group_id, permission_type in group_perms.items():
                    if not permission_type:
                        continue

                    permission_name = "{}_{}_{}".format(
                        permission_type, model_name, field_name
                    )

                    group_permissions.append(
                        Group.permissions.through(
                            group=groups[group_id],
                            permission=permissions[permission_name],
                        )
                    )

        # Delete existing field permissions from the pre-defined groups
        mvj_groups = [grp for grp in groups.values() if grp.id in range(1, 8)]
        Group.permissions.through.objects.filter(
            group__in=mvj_groups, permission__in=all_field_permissions
        ).delete()

        # Save the desired field permissions for the groups
        Group.permissions.through.objects.bulk_create(group_permissions)

        # Logging
        permissions_by_group = defaultdict(list)
        for group_permission in group_permissions:
            permissions_by_group[group_permission.group.name].append(
                group_permission.permission.codename
            )
        for group_name, permissions in permissions_by_group.items():
            self.stdout.write(
                f'Added field permissions for group "{group_name}": {", ".join(permissions)}'
            )
