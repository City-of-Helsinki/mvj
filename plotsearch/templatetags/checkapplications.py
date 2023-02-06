from django import template
from django.utils.safestring import SafeString

register = template.Library()


@register.simple_tag(takes_context=True)
def entry_exists(context, entry):
    if entry is None or entry.entry_section is None:
        return ""
    elif context["object"].answer == entry.entry_section.answer:
        return SafeString("<td>{}</td><td>{}</td>".format(entry.field.label, entry.value))
    else:
        return ""
