import ast

from django import template
from django.utils.translation import ugettext_lazy as _

from forms.models import Choice

register = template.Library()


@register.filter
def visible_section(section, value):
    return section.filter(visible=value)


@register.filter
def visible_field(field, value):
    return field.filter(enabled=value)


@register.simple_tag
def fetch_choice_value(value, field_id):
    if value == "" or value == "[]":
        return "-"
    try:
        choice_value = ast.literal_eval(value)
    except ValueError:
        return "-"

    choices = Choice.objects.filter(field=field_id)
    if isinstance(choice_value, list):
        choices = choices.filter(value__in=choice_value)
    else:
        choices = choices.filter(value=choice_value)
    if not choices.exists():
        if choice_value:
            return _("yes")
        else:
            return _("no")
    return " ".join([choice.text for choice in choices])
