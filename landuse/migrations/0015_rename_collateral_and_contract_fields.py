from django.db import migrations, models

COLLATERAL_TYPE_FROM_LEGACY = {
    "MORTGAGE_DEED": "mortgage_document",
    "CASH_DEPOSIT": "financial_guarantee",
    "PERSONAL_GUARANTEE": "self_debtor_guarantee",
    "DEPOSIT_PLEDGE": "pledge_of_funds",
    "OTHER": "other",
}
COLLATERAL_TYPE_CHOICES = [
    ("mortgage_document", "Panttikirja"),
    ("financial_guarantee", "Rahavakuus"),
    ("self_debtor_guarantee", "Omavelkainen takaus"),
    ("pledge_of_funds", "Tilivarojen panttaus"),
    ("other", "Muu vakuus"),
]
COLLATERAL_MODELS = [
    "mortgagedeedcollateral",
    "cashdepositcollateral",
    "personalguaranteecollateral",
    "depositpledgecollateral",
    "othercollateral",
]


def map_collateral_types(apps, schema_editor):
    for model_name in COLLATERAL_MODELS:
        model = apps.get_model("landuse", model_name)
        for legacy, current in COLLATERAL_TYPE_FROM_LEGACY.items():
            model.objects.filter(collateral_type=legacy).update(collateral_type=current)


def unmap_collateral_types(apps, schema_editor):
    for model_name in COLLATERAL_MODELS:
        model = apps.get_model("landuse", model_name)
        for legacy, current in COLLATERAL_TYPE_FROM_LEGACY.items():
            model.objects.filter(collateral_type=current).update(collateral_type=legacy)


def collateral_base_renames(model_name):
    return [
        migrations.RenameField(model_name, "guarantee_type", "collateral_type"),
        migrations.RenameField(
            model_name, "third_party_pledger_name", "third_party_pledgor_name"
        ),
        migrations.RenameField(
            model_name,
            "third_party_pledger_business_id",
            "third_party_pledgor_business_id",
        ),
        migrations.AlterField(
            model_name,
            "collateral_type",
            models.CharField(choices=COLLATERAL_TYPE_CHOICES),
        ),
    ]


def guarantor_renames(model_name):
    return [
        migrations.RenameField(model_name, "guarantor_name", "pledgor_name"),
        migrations.RenameField(
            model_name, "guarantor_business_id", "pledgor_business_id"
        ),
        migrations.RenameField(
            model_name,
            "guarantor_national_identification_number",
            "pledgor_national_identification_number",
        ),
    ]


class Migration(migrations.Migration):

    dependencies = [
        ("landuse", "0014_add_landuse_auth_groups"),
    ]

    operations = [
        # Contract and contract change
        migrations.RenameField("contract", "identifier", "contract_number"),
        migrations.RenameField(
            "contract", "first_invitation_sent_date", "first_call_sent"
        ),
        migrations.RenameField(
            "contract", "second_invitation_sent_date", "second_call_sent"
        ),
        migrations.RenameField(
            "contract", "third_invitation_sent_date", "third_call_sent"
        ),
        migrations.RenameField("contract", "note", "signing_note"),
        migrations.RenameField("contractchange", "identifier", "contract_number"),
        migrations.RenameField(
            "contractchange", "first_invitation_sent_date", "first_call_sent"
        ),
        migrations.RenameField(
            "contractchange", "second_invitation_sent_date", "second_call_sent"
        ),
        migrations.RenameField(
            "contractchange", "third_invitation_sent_date", "third_call_sent"
        ),
        migrations.RenameField("contractchange", "note", "description"),
        migrations.AlterField(
            model_name="contractchange",
            name="contract",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name="contract_changes",
                to="landuse.contract",
            ),
        ),
        # Collaterals
        *collateral_base_renames("mortgagedeedcollateral"),
        *collateral_base_renames("cashdepositcollateral"),
        *collateral_base_renames("personalguaranteecollateral"),
        *collateral_base_renames("depositpledgecollateral"),
        *collateral_base_renames("othercollateral"),
        *guarantor_renames("cashdepositcollateral"),
        *guarantor_renames("personalguaranteecollateral"),
        *guarantor_renames("depositpledgecollateral"),
        *guarantor_renames("othercollateral"),
        migrations.RenameField(
            "personalguaranteecollateral", "guarantee_identifier", "guarantee_number"
        ),
        migrations.RenameField(
            "mortgagedeedcollateral", "mortgage_deed_number", "mortgage_document_number"
        ),
        migrations.RenameField(
            "mortgagedeedcollateral", "facility_identifier", "institution_identifier"
        ),
        migrations.RenameField(
            "mortgagedeedcollateral",
            "subsequent_pledgee_name",
            "subordinate_pledgee_name",
        ),
        migrations.RenameField(
            "mortgagedeedcollateral",
            "subsequent_pledgee_business_id",
            "subordinate_pledgee_business_id",
        ),
        migrations.RenameField(
            "mortgagedeedcollateral", "document_category", "document_type"
        ),
        migrations.RenameField(
            "personalguaranteecollateral", "document_category", "document_type"
        ),
        migrations.RenameField(
            "depositpledgecollateral", "document_category", "document_type"
        ),
        migrations.RenameField("othercollateral", "document_category", "document_type"),
        migrations.RunPython(map_collateral_types, unmap_collateral_types),
    ]
