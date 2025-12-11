# Manually created

from django.db import migrations, models


def enable_is_received_date_mandatory_for_akv(apps, schema_editor):
    service_unit = apps.get_model("leasing", "ServiceUnit")
    akv_service_unit_id = 2

    service_unit.objects.filter(
        id=akv_service_unit_id,
    ).update(is_received_date_mandatory=True)


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0116_leasetype_is_active"),
    ]

    operations = [
        migrations.AddField(
            model_name="serviceunit",
            name="is_received_date_mandatory",
            field=models.BooleanField(
                default=False,
                help_text="Make 'Application received at' / 'Hakemuksen saapumispäivä' a required field on lease summary page.",
                verbose_name="Require 'Application received at' field on lease summary page?",
            ),
        ),
        migrations.RunPython(
            code=enable_is_received_date_mandatory_for_akv,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
