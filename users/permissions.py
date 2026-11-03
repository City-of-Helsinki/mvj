from users.models import User
from utils.enums import AuthGroupId as AG
from utils.group_permissions import GroupModelPermissions

USERS_GROUP_MODEL_PERMISSIONS: GroupModelPermissions = {
    User: {
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
}
