from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Allows getting keys with string notation, e.g. key with a space in it.
    Which is not possible in django templates by default."""
    return dictionary.get(key)
