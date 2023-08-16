from modeltranslation.translator import TranslationOptions, register

from plotsearch.models import (
    FAQ,
    AreaSearchIntendedUse,
    PlotSearchSubtype,
    PlotSearchType,
)


@register(PlotSearchType)
class PlotSearchTypeTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(PlotSearchSubtype)
class PlotSearchSubtypeTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(AreaSearchIntendedUse)
class IntendedUseTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(FAQ)
class FAQTranslationOptions(TranslationOptions):
    fields = ("question", "answer")
