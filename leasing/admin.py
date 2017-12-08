from django.contrib.gis import admin

from .models import Asset, Lease


class LeaseAdmin(admin.ModelAdmin):
    pass


admin.site.register(Lease, LeaseAdmin)


class AssetAdmin(admin.ModelAdmin):
    pass


admin.site.register(Asset, AssetAdmin)
