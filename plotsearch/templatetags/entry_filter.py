from django import template

register = template.Library()


@register.filter
def filter_answer(qs, answer):
    return qs.filter(entry_section__answer=answer)


@register.filter
def filter_only_parent(qs):
    return qs.filter(parent__isnull=True)
