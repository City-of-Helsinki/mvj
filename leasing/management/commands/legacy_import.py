from django.core.management.base import BaseCommand

from leasing.integrations.legacy import run_import


class Command(BaseCommand):
    help = 'Script for importing from the legacy database'

    def handle(self, *args, **options):
        run_import()
