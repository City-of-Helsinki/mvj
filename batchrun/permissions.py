from batchrun.models import (
    Command,
    Job,
    JobRun,
    JobRunLogEntry,
    JobRunQueueItem,
    ScheduledJob,
    Timezone,
)
from utils.group_permissions import UG, GroupModelPermissions

BATCHRUN_GROUP_MODEL_PERMISSIONS: GroupModelPermissions = {
    Command: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: None,
            UG.SOPIMUSVALMISTELIJA: None,
            UG.SYOTTAJA: None,
            UG.PERINTALAKIMIES: None,
            UG.LASKUTTAJA: None,
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Job: {
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
    JobRun: {
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
    JobRunLogEntry: {
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
    JobRunQueueItem: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: None,
            UG.SOPIMUSVALMISTELIJA: None,
            UG.SYOTTAJA: None,
            UG.PERINTALAKIMIES: None,
            UG.LASKUTTAJA: None,
            UG.PAAKAYTTAJA: ("view",),
        },
        "fields": {},
    },
    ScheduledJob: {
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
    Timezone: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: None,
            UG.SOPIMUSVALMISTELIJA: None,
            UG.SYOTTAJA: None,
            UG.PERINTALAKIMIES: None,
            UG.LASKUTTAJA: None,
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
}
