from modeltranslation.translator import TranslationOptions, register

from plotsearch.models import AreaSearchIntendedUse, PlotSearchSubtype, PlotSearchType


@register(PlotSearchType)
class PlotSearchTypeTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(PlotSearchSubtype)
class PlotSearchSubtypeTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(AreaSearchIntendedUse)
class IntendedUseTranslationOptions(TranslationOptions):
    fields = ("name",)
