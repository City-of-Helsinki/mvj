from django.db import migrations, models

from leasing.models import LandUseAgreementIdentifier


def forwards_func(apps, schema_editor):
    for identifier in LandUseAgreementIdentifier.objects.all():
        identifier.save()


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0040_landuseagreementinvoice_notes"),
    ]

    operations = [
        migrations.AddField(
            model_name="landuseagreementidentifier",
            name="identifier",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="Identifier"
            ),
        ),
        migrations.RunPython(forwards_func, migrations.RunPython.noop),
    ]
