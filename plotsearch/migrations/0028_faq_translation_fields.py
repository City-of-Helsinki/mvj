# Generated by Django 3.2.18 on 2023-08-16 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plotsearch", "0027_faq"),
    ]

    operations = [
        migrations.AddField(
            model_name="faq",
            name="answer_en",
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name="faq",
            name="answer_fi",
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name="faq",
            name="answer_sv",
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name="faq",
            name="question_en",
            field=models.TextField(null=True, unique=True),
        ),
        migrations.AddField(
            model_name="faq",
            name="question_fi",
            field=models.TextField(null=True, unique=True),
        ),
        migrations.AddField(
            model_name="faq",
            name="question_sv",
            field=models.TextField(null=True, unique=True),
        ),
    ]
