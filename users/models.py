from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from helusers.models import AbstractUser
from rest_framework.authtoken.models import Token


class User(AbstractUser):
    recursive_get_related_skip_relations = [
        "auth_token",
        "logentry",
        "emaillog",
        "emaillogs",
        "Emaillog_recipients+",
        "groups",
        "user_permissions",
        "ad_groups",
        "favourite",
        "answer",
        "plotsearch",
        "areasearch",
        "areasearchstatusnote",
        "targetstatus",
        "informationcheck",
    ]

    @admin.display(boolean=True, description=_("Token exists"))
    def has_token(self) -> bool:
        return Token.objects.filter(user=self).exists()
