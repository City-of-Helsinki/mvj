# Manually created

from django.db import migrations


def forwards_func(apps, schema_editor):
    decision_type = apps.get_model("leasing", "DecisionType")

    # Fix typo: "Maanvuorien" -> "Maanvuokrien"
    decision_type.objects.filter(name="Maanvuorien maksukehotus purku-uhalla").update(
        name="Maanvuokrien maksukehotus purku-uhalla"
    )


def reverse_func(apps, schema_editor):
    decision_type = apps.get_model("leasing", "DecisionType")

    # Reverse: "Maanvuokrien" -> "Maanvuorien"
    decision_type.objects.filter(name="Maanvuokrien maksukehotus purku-uhalla").update(
        name="Maanvuorien maksukehotus purku-uhalla"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("leasing", "0123_collectionnote_entire_lease_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
