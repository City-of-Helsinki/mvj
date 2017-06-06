from __future__ import unicode_literals

from django.db import migrations


def remove_areas(apps, schema_editor):
    area_model = apps.get_model('leasing.Area')
    area_model.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('leasing', '0010_auto_20170530_1601'),
    ]

    operations = [migrations.RunPython(remove_areas)]
