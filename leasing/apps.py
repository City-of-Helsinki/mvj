from django.apps import AppConfig


class LeasingConfig(AppConfig):
    name = "leasing"

    def ready(self):
        import leasing.signals  # noqa: F401
