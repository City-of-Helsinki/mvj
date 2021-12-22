from modeltranslation.translator import TranslationOptions, register

from leasing.models import (
    District,
    Financing,
    Hitas,
    IntendedUse,
    Management,
    Municipality,
)
from leasing.models.land_area import LeaseAreaAddress


@register(IntendedUse)
class IntendedUseTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Municipality)
class MunicipalityTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(District)
class DistrictTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Hitas)
class HitasTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Financing)
class FinancingTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Management)
class ManagementTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(LeaseAreaAddress)
class LeaseAreaAddressTranslationOptions(TranslationOptions):
    fields = ("address",)
