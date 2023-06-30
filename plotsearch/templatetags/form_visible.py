from django import template


register = template.Library()


@register.filter
def visible_section(section, value):
    return section.filter(visible=value)

@register.filter
def visible_field(field, value):
    return field.filter(enabled=value)
