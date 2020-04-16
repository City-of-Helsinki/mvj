import json

from django.core.serializers.json import DjangoJSONEncoder
from rest_framework import renderers


class XLSXRenderer(renderers.BaseRenderer):
    media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    format = 'xlsx'
    charset = 'utf-8'
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        # Return JSON response if the view is not a report or when an error occurred
        if renderer_context['view'].action != 'retrieve' or renderer_context['response'].status_code != 200:
            renderer_context['response']['Content-Type'] = 'application/json'
            return json.dumps(data, cls=DjangoJSONEncoder)

        return renderer_context['view'].report.data_as_excel(data)
