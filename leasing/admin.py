from django.contrib import admin

from .models import Application, BuildingFootprint


class BuildingFootprintInline(admin.TabularInline):
    model = BuildingFootprint
    extra = 3


class ApplicationAdmin(admin.ModelAdmin):
    inlines = [BuildingFootprintInline]


admin.site.register(Application, ApplicationAdmin)
