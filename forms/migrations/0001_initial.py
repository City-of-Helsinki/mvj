import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="FieldType",
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
                ("name", models.CharField(max_length=255)),
                ("identifier", models.SlugField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Form",
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
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("is_template", models.BooleanField(default=False)),
                ("title", models.CharField(blank=True, max_length=255)),
            ],
            options={"abstract": False, },
        ),
        migrations.CreateModel(
            name="Section",
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
                ("title", models.CharField(max_length=255)),
                ("identifier", models.SlugField()),
                ("visible", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("add_new_allowed", models.BooleanField(default=False)),
                ("add_new_text", models.CharField(max_length=255)),
                (
                    "form",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sections",
                        to="forms.Form",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subsections",
                        to="forms.Section",
                    ),
                ),
            ],
            options={
                "ordering": ["sort_order"],
                "unique_together": {("form", "identifier")},
            },
        ),
        migrations.CreateModel(
            name="Field",
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
                ("label", models.CharField(max_length=255)),
                ("hint_text", models.CharField(max_length=255)),
                ("identifier", models.SlugField()),
                ("enabled", models.BooleanField(default=True)),
                ("required", models.BooleanField(default=False)),
                ("validation", models.CharField(max_length=255)),
                ("action", models.CharField(max_length=255)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                (
                    "section",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="forms.Section"
                    ),
                ),
                (
                    "type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="forms.FieldType",
                    ),
                ),
            ],
            options={
                "ordering": ["sort_order"],
                "unique_together": {("section", "identifier")},
            },
        ),
        migrations.CreateModel(
            name="Choice",
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
                ("text", models.CharField(max_length=255)),
                ("value", models.CharField(max_length=50)),
                ("action", models.CharField(max_length=255)),
                ("has_text_input", models.BooleanField(default=False)),
                (
                    "field",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="forms.Field"
                    ),
                ),
            ],
        ),
    ]
