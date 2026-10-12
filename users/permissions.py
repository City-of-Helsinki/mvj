from users.models import User
from utils.group_permissions import UG, GroupModelPermissions

USERS_GROUP_MODEL_PERMISSIONS: GroupModelPermissions = {
    User: {
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
}
