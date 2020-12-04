from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="choice",
            name="text_en",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="choice",
            name="text_fi",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="choice",
            name="text_sv",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="field",
            name="hint_text_en",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="field",
            name="hint_text_fi",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="field",
            name="hint_text_sv",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="field",
            name="label_en",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="field",
            name="label_fi",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="field",
            name="label_sv",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="form",
            name="title_en",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="form",
            name="title_fi",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="form",
            name="title_sv",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="section",
            name="add_new_text_en",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="section",
            name="add_new_text_fi",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="section",
            name="add_new_text_sv",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="section",
            name="title_en",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="section",
            name="title_fi",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="section",
            name="title_sv",
            field=models.CharField(max_length=255, null=True),
        ),
    ]
