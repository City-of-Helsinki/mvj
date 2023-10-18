# Generated by Django 3.2.18 on 2023-10-30 12:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("leasing", "0056_attach_usage_distribution_to_plan_unit"),
        ("plotsearch", "0029_alter_areasearch_description_area"),
    ]

    operations = [
        migrations.AddField(
            model_name="areasearch",
            name="lease",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="area_searches",
                to="leasing.lease",
            ),
        ),
        migrations.AddField(
            model_name="targetstatus",
            name="lease",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="target_statuses",
                to="leasing.lease",
            ),
        ),
        migrations.CreateModel(
            name="RelatedPlotApplication",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("deleted", models.DateTimeField(editable=False, null=True)),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Time created"
                    ),
                ),
                (
                    "modified_at",
                    models.DateTimeField(auto_now=True, verbose_name="Time modified"),
                ),
                ("object_id", models.PositiveBigIntegerField()),
                (
                    "content_type",
                    models.ForeignKey(
                        limit_choices_to={"model__in": ["targetstatus", "areasearch"]},
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                    ),
                ),
                (
                    "lease",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="related_plot_applications",
                        to="leasing.lease",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="relatedplotapplication",
            index=models.Index(
                fields=["content_type", "object_id"],
                name="plotsearch__content_73ff67_idx",
            ),
        ),
    ]
