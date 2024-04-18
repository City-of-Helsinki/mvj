from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

GROUPS = [
    # User roles
    "Selailija",
    "Valmistelija",
    "Sopimusvalmistelija",
    "Syöttäjä",
    "Perintälakimies",
    "Laskuttaja",
    "Pääkäyttäjä",
    # Service units
    "Maaomaisuuden kehittäminen ja tontit",
    "Alueiden käyttö ja valvonta",
    "KuVa / Liikuntapaikkapalvelut",
    "KuVa / Ulkoilupalvelut",
    "KuVa / Nuorisopalvelut",
]


class Command(BaseCommand):
    """
    Makes copies of GROUPS with the same permissions.
    The test groups are named "TEST <group name>".
    Since groups are synced from AD groups and flushed periodically,
    this is a way to make permissions stick for e.g. devs.
    """

    def handle(self, *args, **options):
        groups = Group.objects.filter(name__in=GROUPS)
        for group in groups:
            test_group_name = f"TEST {group.name}"
            (test_group, created) = Group.objects.get_or_create(
                name=test_group_name,
                defaults={"id": group.id + 1000, "name": test_group_name},
            )
            test_group.permissions.set(group.permissions.all())
