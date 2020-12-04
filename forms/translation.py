from modeltranslation.translator import TranslationOptions, register

from .models import Choice, Field, Form, Section


@register(Form)
class FormTranslationOptions(TranslationOptions):
    fields = ("title",)


@register(Section)
class SectionTranslationOptions(TranslationOptions):
    fields = ("title", "add_new_text")


@register(Field)
class FieldTranslationOptions(TranslationOptions):
    fields = (
        "label",
        "hint_text",
    )


@register(Choice)
class ChoiceTranslationOptions(TranslationOptions):
    fields = ("text",)
