from django.apps import AppConfig


class PlotsearchConfig(AppConfig):
    name = "plotsearch"

    def ready(self):
        import plotsearch.signals  # noqa: F401
