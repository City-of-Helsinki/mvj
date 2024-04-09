from django.db import migrations, models


def _generate_identifier(landuse_agreement_identifier):
    """Returns the land use agreement identifier as a string
    The Land use agreement identifier is constructed out of the type identifier, municipality,
    district, and sequence, in that order. For example, the identifier
    for a land use agreement (MA) in Helsinki (1), Vallila (22), and sequence
    number 1 would be MA122-1.
    """
    return "{}{}{:02}-{}".format(
        landuse_agreement_identifier.type.identifier,
        landuse_agreement_identifier.municipality.identifier,
        int(landuse_agreement_identifier.district.identifier),
        landuse_agreement_identifier.sequence,
    )


def forwards_func(apps, schema_editor):
    LandUseAgreementIdentifier = apps.get_model(  # NOQA: N806
        "leasing", "LandUseAgreementIdentifier"
    )

    for landuse_agreement_identifier in LandUseAgreementIdentifier.objects.all():
        landuse_agreement_identifier.identifier = _generate_identifier(
            landuse_agreement_identifier
        )
        landuse_agreement_identifier.save()


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0040_landuseagreementinvoice_notes"),
    ]

    operations = [
        migrations.AddField(
            model_name="landuseagreementidentifier",
            name="identifier",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="Identifier"
            ),
        ),
        migrations.RunPython(forwards_func, migrations.RunPython.noop),
    ]
