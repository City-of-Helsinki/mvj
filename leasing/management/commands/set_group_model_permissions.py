from collections import defaultdict

from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

# 1 Selailija
# 2 Valmistelija
# 3 Sopimusvalmistelija
# 4 Syöttäjä
# 5 Perintälakimies
# 6 Laskuttaja
# 7 Pääkäyttäjä

DEFAULT_MODEL_PERMS = {
    # "areasource": {
    # },
    # "area": {
    # },
    "areanote": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "decisionmaker": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "decisiontype": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "decision": {
        1: ("view",),
        2: ("view", "change"),
        3: ("view", "change"),
        4: ("view", "add", "change", "delete"),
        5: ("view", "change"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "conditiontype": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "condition": {
        1: ("view",),
        2: ("view", "change"),
        3: ("view", "change"),
        4: ("view", "add", "change", "delete"),
        5: ("view", "change"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "creditdecision": {
        1: None,
        2: (
            "view",
            "send_creditdecision_inquiry",
            "send_sanctions_inquiry",
        ),
        3: (
            "view",
            "send_creditdecision_inquiry",
            "send_sanctions_inquiry",
        ),
        4: (
            "view",
            "send_creditdecision_inquiry",
            "send_sanctions_inquiry",
        ),
        5: (
            "view",
            "send_creditdecision_inquiry",
            "send_sanctions_inquiry",
        ),
        6: (
            "view",
            "send_creditdecision_inquiry",
            "send_sanctions_inquiry",
        ),
        7: (
            "view",
            "add",
            "change",
            "delete",
            "send_creditdecision_inquiry",
            "send_sanctions_inquiry",
        ),
    },
    "creditdecisionreason": {
        1: None,
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "creditdecisionlog": {
        1: None,
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "rentintendeduse": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "rent": {
        1: ("view",),
        2: ("view", "change"),
        3: ("view", "change"),
        4: ("view", "add", "change", "delete"),
        5: ("view", "change"),
        6: ("view", "change"),
        7: ("view", "add", "change", "delete"),
    },
    "rentduedate": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view", "add", "change", "delete"),
        7: ("view", "add", "change", "delete"),
    },
    "fixedinitialyearrent": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "contractrent": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "indexadjustedrent": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "equalizedrent": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view",),
    },
    "rentadjustment": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view", "add", "change", "delete"),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "managementsubvention": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view", "add", "change", "delete"),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "managementsubventionformofmanagement": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view", "add", "change", "delete"),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "temporarysubvention": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view", "add", "change", "delete"),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "payablerent": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "index": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "leasebasisofrent": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "leasebasisofrentmanagementsubvention": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "leasebasisofrenttemporarysubvention": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "basisofrentplottype": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "basisofrentbuildpermissiontype": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "basisofrent": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "basisofrentrate": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "basisofrentpropertyidentifier": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "basisofrentdecision": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "commenttopic": {
        1: None,
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "comment": {
        1: None,
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view", "add", "change", "delete"),
        7: ("view", "add", "change", "delete"),
    },
    "contact": {
        1: ("view",),
        2: ("view", "change"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "change"),
        6: ("view", "add", "change", "delete"),
        7: ("view", "add", "change", "delete"),
    },
    "contracttype": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "contract": {
        1: ("view",),
        2: ("view", "change"),
        3: ("view", "add", "change", "delete"),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view", "change"),
        7: ("view", "add", "change", "delete"),
    },
    "collateral": {
        1: ("view",),
        2: ("view",),
        3: ("view", "add", "change", "delete"),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view", "add", "change", "delete"),
        7: ("view", "add", "change", "delete"),
    },
    "collateraltype": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "contractchange": {
        1: ("view",),
        2: ("view",),
        3: ("view", "add", "change", "delete"),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "collectionletter": {
        1: None,
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "collectionlettertemplate": {
        1: None,
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "collectionnote": {
        1: None,
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view", "add", "change", "delete"),
        6: ("view", "add", "change", "delete"),
        7: ("view", "add", "change", "delete"),
    },
    "collectioncourtdecision": {
        1: None,
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "customdetailedplan": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "interestrate": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "leasetype": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "municipality": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "district": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "areasearchintendeduse": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "intendeduse": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "statisticaluse": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "supportivehousing": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "financing": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "management": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "regulation": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "hitas": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "noticeperiod": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "specialproject": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "reservationprocedure": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "leaseidentifier": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "lease": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view", "change"),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view", "change"),
        7: ("view", "add", "change", "delete", "delete_nonempty"),
    },
    "leasestatelog": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view",),
    },
    "relatedlease": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "infilldevelopmentcompensation": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "infilldevelopmentcompensationlease": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "infilldevelopmentcompensationdecision": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "infilldevelopmentcompensationintendeduse": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "infilldevelopmentcompensationattachment": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "inspection": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "inspectionattachment": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "receivabletype": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "invoiceset": {
        1: None,
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view", "add", "change", "delete"),
        7: ("view", "add", "change", "delete"),
    },
    "invoice": {
        1: None,
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view", "add", "change", "delete"),
        7: ("view", "add", "change", "delete"),
    },
    "invoicerow": {
        1: None,
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view", "add", "change", "delete"),
        7: ("view", "add", "change", "delete"),
    },
    "invoicenote": {
        1: None,
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view", "add", "change", "delete"),
        7: ("view", "add", "change", "delete"),
    },
    "invoicepayment": {
        1: None,
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view", "add", "change", "delete"),
        7: ("view", "add", "change", "delete"),
    },
    "leasearea": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "leaseholdtransfer": {
        1: ("view",),
        2: ("view",),
        3: ("view", "delete"),
        4: ("view", "delete"),
        5: ("view",),
        6: ("view",),
        7: ("view", "delete"),
    },
    "leaseholdtransferparty": {
        1: ("view",),
        2: ("view",),
        3: ("view", "delete"),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "delete"),
    },
    "leaseholdtransferproperty": {
        1: ("view",),
        2: ("view",),
        3: ("view", "delete"),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "delete"),
    },
    "leaseareaaddress": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "leaseareaattachment": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "constructabilitydescription": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "plot": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "plotsearch": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "plotsearchstage": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "plotsearchtype": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    # TODO These are copypasted from above
    "plotsearchsubtype": {
        1: None,
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "targetstatus": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "usagedistribution": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "areasearch": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "informationcheck": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "relatedplotapplication": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "planunittype": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "plotdivisionstate": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "planunitstate": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "planunitintendeduse": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "planunit": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "serviceunit": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view",),
    },
    "tenant": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view", "change"),
        7: ("view", "add", "change", "delete"),
    },
    "tenantcontact": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view", "add", "change"),
        7: ("view", "add", "change", "delete"),
    },
    "tenantrentshare": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view", "add", "change"),
        7: ("view", "add", "change", "delete"),
    },
    "vat": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "olddwellingsinhousingcompaniespriceindex": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "applicationmetadata": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "uidata": {
        1: ("view", "add", "change", "delete"),
        2: ("view", "add", "change", "delete"),
        3: ("view", "add", "change", "delete"),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view", "add", "change", "delete"),
        7: ("view", "add", "change", "delete", "edit_global_ui_data"),
    },
    "user": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view",),
    },
    "landuseagreement": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "landuseagreementattachment": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "landuseagreementinvoice": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view", "add", "change", "delete"),
        7: ("view", "add", "change", "delete"),
    },
    "landuseagreementinvoicepayment": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view", "add", "change", "delete"),
        7: ("view", "add", "change", "delete"),
    },
    "landuseagreementinvoicerow": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view", "add", "change", "delete"),
        7: ("view", "add", "change", "delete"),
    },
    "landuseagreementinvoiceset": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view", "add", "change", "delete"),
        7: ("view", "add", "change", "delete"),
    },
    "landuseagreementlitigant": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view", "add", "change", "delete"),
        7: ("view", "add", "change", "delete"),
    },
    "landuseagreementcondition": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "landuseagreementcompensation": {
        1: ("view",),
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "landuseagreementdecision": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "landuseagreementdecisioncondition": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "landuseagreementreceivabletype": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    # Batchrun
    "command": {
        1: None,
        2: None,
        3: None,
        4: None,
        5: None,
        6: None,
        7: ("view", "add", "change", "delete"),
    },
    "job": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "jobrun": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view",),
    },
    "jobrunlogentry": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view",),
    },
    "jobrunqueueitem": {
        1: None,
        2: None,
        3: None,
        4: None,
        5: None,
        6: None,
        7: ("view",),
    },
    "scheduledjob": {
        1: ("view",),
        2: ("view",),
        3: ("view",),
        4: ("view",),
        5: ("view",),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "timezone": {
        1: None,
        2: None,
        3: None,
        4: None,
        5: None,
        6: None,
        7: ("view", "add", "change", "delete"),
    },
    # TODO These are copypasted from plotsearch
    "form": {
        1: None,
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "answer": {
        1: None,
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "attachment": {
        1: None,
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    "areasearchattachment": {
        1: ("view",),
        2: ("view", "add"),
        3: ("view",),
        4: ("view", "add"),
        5: ("view", "add"),
        6: ("view",),
        7: ("view", "add"),
    },
    "meetingmemo": {
        1: None,
        2: ("view", "add", "change", "delete"),
        3: ("view",),
        4: ("view", "add", "change", "delete"),
        5: ("view", "add", "change", "delete"),
        6: ("view",),
        7: ("view", "add", "change", "delete"),
    },
    # leasing.report_storage
    "reportstorage": {
        1: None,
        2: None,
        3: None,
        4: None,
        5: None,
        6: None,
        7: ("view", "delete"),
    },
}

PERMISSION_TYPES = ("view", "add", "change", "delete")


class Command(BaseCommand):
    help = "Sets predefined model permissions for the predefined MVJ groups"

    def handle(self, *args, **options):  # NOQA
        groups = {group.id: group for group in Group.objects.all()}
        permissions = {perm.codename: perm for perm in Permission.objects.all()}

        all_model_permissions = []
        group_permissions = []
        app_names = [
            "credit_integration",
            "leasing",
            "users",
            "batchrun",
            "plotsearch",
            "forms",
        ]

        for app_name in app_names:
            for model in apps.get_app_config(app_name).get_models(
                include_auto_created=True
            ):
                model_name = model._meta.model_name

                if model_name not in DEFAULT_MODEL_PERMS:
                    self.stdout.write(
                        'Model "{}" not in DEFAULT_MODEL_PERMS. Skipping.'.format(
                            model_name
                        )
                    )
                    continue

                for permission_type in PERMISSION_TYPES:
                    all_model_permissions.append(
                        permissions["{}_{}".format(permission_type, model_name)]
                    )

                for custom_model_permission_name, desc in model._meta.permissions:
                    all_model_permissions.append(
                        permissions[custom_model_permission_name]
                    )

                for group_id, permission_types in DEFAULT_MODEL_PERMS[
                    model_name
                ].items():
                    if not permission_types:
                        continue

                    for permission_type in permission_types:
                        if permission_type in permissions:
                            permission = permissions[permission_type]
                        else:
                            permission = permissions[
                                "{}_{}".format(permission_type, model_name)
                            ]

                        group_permissions.append(
                            Group.permissions.through(
                                group=groups[group_id], permission=permission
                            )
                        )

        # Delete existing group permissions from the pre-defined groups
        mvj_groups = [grp for grp in groups.values() if grp.id in range(1, 8)]
        Group.permissions.through.objects.filter(
            group__in=mvj_groups, permission__in=all_model_permissions
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
                f'Added model permissions for group "{group_name}": {", ".join(permissions)}'
            )
