from django.core.management.base import BaseCommand

import cx_Oracle
from leasing.importer.basis_of_rent import BasisOfRentImporter
from leasing.importer.lease import LeaseImporter


class Command(BaseCommand):
    help = 'Import data from the old MVJ database'

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

        self.importers = [
            BasisOfRentImporter,
            LeaseImporter,
        ]

        self._importers = {}
        for importer in self.importers:
            self._importers[importer.type_name] = importer

    def add_arguments(self, parser):
        importer_choices = self._importers.keys()

        parser.add_argument('types', nargs='+', type=str, choices=importer_choices, help='types of data to import')

        for importer in self.importers:
            importer.add_arguments(parser)

    def handle(self, *args, **options):
        connection = cx_Oracle.connect(user='mvj', password='mvjpass', dsn='localhost:1521/ORCLPDB1', encoding="UTF-8",
                                       nencoding="UTF-8")

        cursor = connection.cursor()

        for importer_type_name in options['types']:
            importer = self._importers[importer_type_name](cursor=cursor, stdout=self.stdout)
            importer.read_options(options)
            importer.execute()
