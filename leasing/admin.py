from django.contrib.gis import admin

from .models import Asset, Lease


class LeaseAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': (
                'type',
                'municipality',
                'district',
                'sequence',
                'start_date',
                'end_date',
            )
        }),
    )

    readonly_fields = ('created_at', 'modified_at')


admin.site.register(Lease, LeaseAdmin)


class AssetAdmin(admin.ModelAdmin):
    pass


admin.site.register(Asset, AssetAdmin)
