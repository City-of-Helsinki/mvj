import base64

from django import template
from django.contrib.staticfiles import finders
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def base64_image(image_path):
    full_path = finders.find(image_path)
    with open(full_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return mark_safe(f"data:image/png;base64,{encoded_string}")
