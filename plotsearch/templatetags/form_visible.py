from django import template

from forms.models import Choice

register = template.Library()


@register.filter
def visible_section(section, value):
    return section.filter(visible=value)

@register.filter
def visible_field(field, value):
    return field.filter(enabled=value)

@register.simple_tag
def fetch_choice_value(value):
    try:
        choice = Choice.objects.get(id=value).value
    except ValueError:
        choice = "-"
    return choice
