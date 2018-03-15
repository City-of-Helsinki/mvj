from rest_framework.renderers import BrowsableAPIRenderer


# From: https://bradmontgomery.net/blog/disabling-forms-django-rest-frameworks-browsable-api/
class BrowsableAPIRendererWithoutForms(BrowsableAPIRenderer):
    """Renders the browsable api, but excludes the html form."""

    def get_context(self, *args, **kwargs):
        ctx = super().get_context(*args, **kwargs)
        return ctx

    def get_rendered_html_form(self, data, view, method, request):
        """Returns empty html for the html form, except True for DELETE
        and OPTIONS methods to show buttons for them"""

        if method in ('DELETE', 'OPTIONS'):
            return True

        return ""
