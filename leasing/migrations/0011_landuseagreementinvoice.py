# Generated by Django 2.2.13 on 2020-08-24 13:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("leasing", "0010_add_plot_search_base"),
    ]

    operations = [
        migrations.CreateModel(
            name="LandUseAgreementInvoice",
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
                (
                    "number",
                    models.PositiveIntegerField(
                        blank=True, null=True, unique=True, verbose_name="Number"
                    ),
                ),
                (
                    "compensation_amount",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        verbose_name="Compensation amount",
                    ),
                ),
                (
                    "compensation_amount_percentage",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        verbose_name="Compensation amount percentage",
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2, max_digits=12, verbose_name="Amount"
                    ),
                ),
                (
                    "sign_date",
                    models.DateField(blank=True, null=True, verbose_name="Sign date"),
                ),
                (
                    "plan_lawfulness_date",
                    models.DateField(
                        blank=True, null=True, verbose_name="Plan lawfulness date"
                    ),
                ),
                (
                    "due_date",
                    models.DateField(blank=True, null=True, verbose_name=" date"),
                ),
                (
                    "sent_date",
                    models.DateField(blank=True, null=True, verbose_name="Sent date"),
                ),
                (
                    "paid_date",
                    models.DateField(blank=True, null=True, verbose_name="Paid date"),
                ),
                (
                    "sent_to_sap_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Sent to SAP at"
                    ),
                ),
                (
                    "land_use_agreement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="invoices",
                        to="leasing.LandUseAgreement",
                        verbose_name="Land use agreement",
                    ),
                ),
                (
                    "recipient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="leasing.Contact",
                        verbose_name="Recipient",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
