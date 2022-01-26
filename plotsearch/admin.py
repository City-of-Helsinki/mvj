# Register your models here.
from django.contrib.gis import admin

from field_permissions.admin import FieldPermissionsAdminMixin
from leasing.admin import NameAdmin
from plotsearch.models import (
    Favourite,
    FavouriteTarget,
    PlotSearch,
    PlotSearchStage,
    PlotSearchSubtype,
    PlotSearchType,
)


class PlotSearchAdmin(FieldPermissionsAdminMixin, admin.ModelAdmin):
    list_display = ("name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related("subtype", "stage",)


class FavouriteTargetInline(FieldPermissionsAdminMixin, admin.TabularInline):
    model = FavouriteTarget


class FavouriteAdmin(FieldPermissionsAdminMixin, admin.ModelAdmin):
    list_display = ("user", "created_at", "modified_at")
    inlines = [FavouriteTargetInline]


admin.site.register(PlotSearch, PlotSearchAdmin)
admin.site.register(PlotSearchStage, NameAdmin)
admin.site.register(Favourite, FavouriteAdmin)
admin.site.register(PlotSearchSubtype, NameAdmin)
admin.site.register(PlotSearchType, NameAdmin)
