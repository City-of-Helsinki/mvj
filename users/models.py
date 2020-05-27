from helusers.models import AbstractUser


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
    ]
