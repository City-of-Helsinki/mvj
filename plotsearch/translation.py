from modeltranslation.translator import TranslationOptions, register

from plotsearch.models import IntendedUse, PlotSearchSubtype, PlotSearchType


@register(PlotSearchType)
class PlotSearchTypeTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(PlotSearchSubtype)
class PlotSearchSubtypeTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(IntendedUse)
class IntendedUseTranslationOptions(TranslationOptions):
    fields = ("name",)
