from django.apps import AppConfig
from django.contrib.auth import user_logged_in


class UsersConfig(AppConfig):
    name = "users"

    def ready(self):
        from . import signals

        user_logged_in.connect(
            signals.user_logged_in, dispatch_uid="users_signals_user_logged_in"
        )
