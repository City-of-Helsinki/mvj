import ast

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
def fetch_choice_value(value, field_id):
    if value == "" or value == "[]":
        return "-"
    choice_value = ast.literal_eval(value)
    choices = Choice.objects.filter(field=field_id)
    if isinstance(choice_value, list):
        choices = choices.filter(value__in=choice_value)
    else:
        choices = choices.filter(value=choice_value)
    if not choices.exists():
        return "-"
    return " ".join([choice.text for choice in choices])
