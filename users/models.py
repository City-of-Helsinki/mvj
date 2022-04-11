from django.db import models
from helusers.models import AbstractUser


class User(AbstractUser):
    service_units = models.ManyToManyField("leasing.ServiceUnit", related_name="users")

    recursive_get_related_skip_relations = [
        "auth_token",
        "logentry",
        "emaillog",
        "emaillogs",
        "Emaillog_recipients+",
        "groups",
        "user_permissions",
        "ad_groups",
    ]
