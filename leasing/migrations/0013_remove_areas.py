from __future__ import unicode_literals

from django.db import migrations


def remove_areas(apps, schema_editor):
    area_model = apps.get_model('leasing.Area')
    area_model.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('leasing', '0012_srid_change'),
    ]

    operations = [migrations.RunPython(remove_areas)]
