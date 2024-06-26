# Register your models here.
from django.contrib.gis import admin

from field_permissions.admin import FieldPermissionsAdminMixin
from leasing.admin import NameAdmin
from plotsearch.models import (
    AreaSearchIntendedUse,
    Favourite,
    FavouriteTarget,
    PlotSearch,
    PlotSearchStage,
    PlotSearchSubtype,
    PlotSearchType,
)
from plotsearch.models.plot_search import FAQ


class PlotSearchAdmin(FieldPermissionsAdminMixin, admin.ModelAdmin):
    list_display = ("name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related(
            "stage",
        )


class FavouriteTargetInline(FieldPermissionsAdminMixin, admin.TabularInline):
    model = FavouriteTarget


class FavouriteAdmin(FieldPermissionsAdminMixin, admin.ModelAdmin):
    list_display = ("user", "created_at", "modified_at")
    inlines = [FavouriteTargetInline]


class FAQAdmin(admin.ModelAdmin):
    list_display = (
        "question_truncate",
        "answer_truncate",
    )


admin.site.register(PlotSearch, PlotSearchAdmin)
admin.site.register(PlotSearchStage, NameAdmin)
admin.site.register(Favourite, FavouriteAdmin)
admin.site.register(PlotSearchType, NameAdmin)
admin.site.register(AreaSearchIntendedUse, NameAdmin)
admin.site.register(PlotSearchSubtype, NameAdmin)
admin.site.register(FAQ, FAQAdmin)
