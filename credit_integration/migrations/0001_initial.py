import credit_integration.enums
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import enumfields.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("leasing", "0045_move_plotsearch_to_plotsearch_app"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CreditDecisionReason",
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
                    "reason_code",
                    models.CharField(
                        max_length=3, unique=True, verbose_name="Reason code"
                    ),
                ),
                ("reason", models.TextField(verbose_name="Reason")),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="CreditDecision",
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
                    "status",
                    enumfields.fields.EnumField(
                        enum=credit_integration.enums.CreditDecisionStatus,
                        max_length=30,
                        verbose_name="Status",
                    ),
                ),
                (
                    "business_id",
                    models.CharField(
                        blank=True, max_length=9, verbose_name="Business ID"
                    ),
                ),
                (
                    "official_name",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="Official name"
                    ),
                ),
                (
                    "address",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="Address"
                    ),
                ),
                (
                    "phone_number",
                    models.CharField(
                        blank=True, max_length=50, verbose_name="Phone number"
                    ),
                ),
                (
                    "business_entity",
                    models.CharField(
                        blank=True, max_length=50, verbose_name="Business entity"
                    ),
                ),
                (
                    "operation_start_date",
                    models.DateField(
                        blank=True, verbose_name="Date of commencement of operations"
                    ),
                ),
                (
                    "industry_code",
                    models.CharField(
                        blank=True, max_length=10, verbose_name="Industry code"
                    ),
                ),
                (
                    "claimant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="credit_decisions",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Claimant",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="credit_decisions",
                        to="leasing.Contact",
                        verbose_name="Customer",
                    ),
                ),
                (
                    "reasons",
                    models.ManyToManyField(
                        to="credit_integration.CreditDecisionReason",
                        verbose_name="Reasons",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
