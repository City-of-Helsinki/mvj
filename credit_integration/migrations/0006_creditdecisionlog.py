import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("credit_integration", "0005_creditdecision_original_data"),
    ]

    operations = [
        migrations.CreateModel(
            name="CreditDecisionLog",
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
                (
                    "identification",
                    models.CharField(max_length=20, verbose_name="Identification"),
                ),
                ("text", models.CharField(max_length=255, verbose_name="Text")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="credit_decision_logs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "Credit decision log",
                "verbose_name_plural": "Credit decision logs",
                "ordering": ["-created_at"],
            },
        ),
    ]
