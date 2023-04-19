from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
GROUPS = {
    1: "Selailija test",
    2: "Valmistelija test",
    3: "Sopimusvalmistelija test",
    4: "Syöttäjä test",
    5: "Perintälakimies test",
    6: "Laskuttaja test",
    7: "Pääkäyttäjä test",
}
class Command(BaseCommand):
    def handle(self, *args, **options):
        for group in Group.objects.filter(id__in=GROUPS.keys()):
            (new_group, created) = Group.objects.get_or_create(
id=group.id + 10, defaults={"name": GROUPS[group.id]} )
            new_group.permissions.set(group.permissions.all())
