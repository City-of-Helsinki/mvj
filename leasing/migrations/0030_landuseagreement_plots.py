from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0029_refactor_master_land_item"),
    ]

    operations = [
        migrations.AddField(
            model_name="landuseagreement",
            name="plots",
            field=models.ManyToManyField(to="leasing.Plot"),
        ),
    ]
