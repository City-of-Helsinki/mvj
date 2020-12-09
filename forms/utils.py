from django.utils.text import slugify


def generate_unique_identifier(klass, field, max_length):
    origin_identifier = slugify(field)[:max_length]
    unique_identifier = origin_identifier
    index = 1
    while klass.objects.filter(identifier=unique_identifier).exists():
        unique_identifier = "{}-{}".format(
            origin_identifier[: max_length - len(str(index)) - 1], index
        )
        index += 1
    return unique_identifier
