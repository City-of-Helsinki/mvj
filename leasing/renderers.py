from rest_framework.renderers import BrowsableAPIRenderer


class BrowsableAPIRendererWithoutHtmlForm(BrowsableAPIRenderer):
    """Renders the browsable api, but excludes the html form."""

    def get_context(self, *args, **kwargs):
        ctx = super().get_context(*args, **kwargs)
        return ctx

    def get_rendered_html_form(self, data, view, method, request):
        return ""
