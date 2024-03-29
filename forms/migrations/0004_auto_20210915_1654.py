# Generated by Django 2.2.13 on 2021-09-15 13:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0003_answer_entry"),
    ]

    operations = [
        migrations.AlterField(
            model_name="entry",
            name="answer",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="entries",
                to="forms.Answer",
            ),
        ),
    ]
