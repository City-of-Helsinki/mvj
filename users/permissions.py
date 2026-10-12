from utils.group_permissions import UG

USERS_GROUP_MODEL_PERMISSIONS = {
    "user": {
        UG.SELAILIJA: ("view",),
        UG.VALMISTELIJA: ("view",),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view",),
        UG.PERINTALAKIMIES: ("view",),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view",),
    },
}
