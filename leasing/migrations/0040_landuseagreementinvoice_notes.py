from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0039_landuseagreementinvoice_postpone_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="landuseagreementinvoice",
            name="notes",
            field=models.TextField(blank=True, verbose_name="Notes"),
        ),
    ]
