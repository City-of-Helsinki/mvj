from batchrun.models import (
    Command,
    Job,
    JobRun,
    JobRunLogEntry,
    JobRunQueueItem,
    ScheduledJob,
    Timezone,
)
from utils.enums import AuthGroupId as AG
from utils.group_permissions import GroupModelPermissions

BATCHRUN_GROUP_MODEL_PERMISSIONS: GroupModelPermissions = {
    Command: {
        "model": {
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: None,
            AG.SOPIMUSVALMISTELIJA: None,
            AG.SYOTTAJA: None,
            AG.PERINTALAKIMIES: None,
            AG.LASKUTTAJA: None,
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Job: {
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
    JobRun: {
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
    JobRunLogEntry: {
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
    JobRunQueueItem: {
        "model": {
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: None,
            AG.SOPIMUSVALMISTELIJA: None,
            AG.SYOTTAJA: None,
            AG.PERINTALAKIMIES: None,
            AG.LASKUTTAJA: None,
            AG.PAAKAYTTAJA: ("view",),
        },
        "fields": {},
    },
    ScheduledJob: {
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
    Timezone: {
        "model": {
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: None,
            AG.SOPIMUSVALMISTELIJA: None,
            AG.SYOTTAJA: None,
            AG.PERINTALAKIMIES: None,
            AG.LASKUTTAJA: None,
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
}
