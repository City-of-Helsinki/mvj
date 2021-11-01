import django.contrib.postgres.fields.jsonb
import django.core.serializers.json
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("credit_integration", "0004_set_operational_start_date_nullable"),
    ]

    operations = [
        migrations.AddField(
            model_name="creditdecision",
            name="original_data",
            field=django.contrib.postgres.fields.jsonb.JSONField(
                blank=True,
                encoder=django.core.serializers.json.DjangoJSONEncoder,
                null=True,
                verbose_name="original_data",
            ),
        ),
    ]
