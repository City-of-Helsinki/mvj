import django.db.models.deletion
import enumfields.fields
from django.db import migrations, models

import leasing.enums


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0031_landuseagreementattachment"),
    ]

    operations = [
        migrations.CreateModel(
            name="LandUseAgreementReceivableType",
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
                ("name", models.CharField(max_length=255, verbose_name="Name")),
                (
                    "sap_material_code",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="SAP material code",
                    ),
                ),
                (
                    "sap_order_item_number",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="SAP order item number",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Is active?"),
                ),
            ],
            options={
                "verbose_name": "Receivable type",
                "verbose_name_plural": "Receivable types",
            },
        ),
        migrations.RemoveField(model_name="landuseagreementinvoice", name="amount",),
        migrations.RemoveField(
            model_name="landuseagreementinvoice", name="compensation_amount",
        ),
        migrations.RemoveField(
            model_name="landuseagreementinvoice", name="compensation_amount_percentage",
        ),
        migrations.RemoveField(
            model_name="landuseagreementinvoice", name="plan_lawfulness_date",
        ),
        migrations.RemoveField(model_name="landuseagreementinvoice", name="sign_date",),
        migrations.AddField(
            model_name="landuseagreementinvoice",
            name="billed_amount",
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=10, verbose_name="Billed amount"
            ),
        ),
        migrations.AddField(
            model_name="landuseagreementinvoice",
            name="invoicing_date",
            field=models.DateField(
                blank=True, null=True, verbose_name="Invoicing date"
            ),
        ),
        migrations.AddField(
            model_name="landuseagreementinvoice",
            name="outstanding_amount",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=10,
                verbose_name="Outstanding amount",
            ),
        ),
        migrations.AddField(
            model_name="landuseagreementinvoice",
            name="state",
            field=enumfields.fields.EnumField(
                default="open",
                enum=leasing.enums.InvoiceState,
                max_length=30,
                verbose_name="State",
            ),
        ),
        migrations.AddField(
            model_name="landuseagreementinvoice",
            name="total_amount",
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=10, verbose_name="Total amount"
            ),
        ),
        migrations.AddField(
            model_name="landuseagreementinvoice",
            name="type",
            field=enumfields.fields.EnumField(
                default="charge",
                enum=leasing.enums.InvoiceType,
                max_length=30,
                verbose_name="Type",
            ),
        ),
        migrations.AlterField(
            model_name="landuseagreementinvoice",
            name="due_date",
            field=models.DateField(blank=True, null=True, verbose_name="Due date"),
        ),
        migrations.CreateModel(
            name="LandUseAgreementInvoiceRow",
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
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=10,
                        verbose_name="Amount",
                    ),
                ),
                (
                    "compensation_amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        verbose_name="Compensation amount",
                    ),
                ),
                (
                    "description",
                    models.TextField(blank=True, null=True, verbose_name="Description"),
                ),
                (
                    "increase_percentage",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        verbose_name="Increase percentage",
                    ),
                ),
                (
                    "plan_lawfulness_date",
                    models.DateField(
                        blank=True, null=True, verbose_name="Plan lawfulness date"
                    ),
                ),
                (
                    "sign_date",
                    models.DateField(blank=True, null=True, verbose_name="Sign date"),
                ),
                (
                    "invoice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rows",
                        to="leasing.LandUseAgreementInvoice",
                        verbose_name="Invoice",
                    ),
                ),
                (
                    "litigant",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="leasing.LandUseAgreementLitigant",
                        verbose_name="Litigant",
                    ),
                ),
                (
                    "receivable_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="leasing.LandUseAgreementReceivableType",
                        verbose_name="Receivable type",
                    ),
                ),
            ],
            options={
                "verbose_name": "Invoice row",
                "verbose_name_plural": "Invoice rows",
            },
        ),
        migrations.CreateModel(
            name="LandUseAgreementInvoicePayment",
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
                    "paid_amount",
                    models.DecimalField(
                        decimal_places=2, max_digits=10, verbose_name="Paid amount"
                    ),
                ),
                ("paid_date", models.DateField(verbose_name="Paid date")),
                (
                    "filing_code",
                    models.CharField(
                        blank=True, max_length=35, null=True, verbose_name="Name"
                    ),
                ),
                (
                    "invoice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payments",
                        to="leasing.LandUseAgreementInvoice",
                        verbose_name="Invoice",
                    ),
                ),
            ],
            options={
                "verbose_name": "Invoice payment",
                "verbose_name_plural": "Invoice payments",
            },
        ),
    ]
