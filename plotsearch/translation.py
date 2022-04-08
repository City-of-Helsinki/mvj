from modeltranslation.translator import TranslationOptions, register

from plotsearch.models import (
    IntendedSubUse,
    IntendedUse,
    PlotSearchSubtype,
    PlotSearchType,
)


@register(PlotSearchType)
class PlotSearchTypeTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(PlotSearchSubtype)
class PlotSearchSubtypeTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(IntendedUse)
class IntendedUseTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(IntendedSubUse)
class IntendedSubUseTranslationOptions(TranslationOptions):
    fields = ("name",)
