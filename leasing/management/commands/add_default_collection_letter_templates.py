import argparse
import os
import tempfile
from pathlib import Path
from shutil import copyfile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from leasing.models import CollectionLetterTemplate

TEMPLATE_NAMES = {
    "Irtisanomis- ja oikeudenkäyntiuhalla, tilapäinen yritystontti": {
        "filename": "irtisanomis_ja_oikeudenkayntiuhka_tilapainen_yritystontti_template.docx"
    },
    "Purku- ja oikeudenkäyntiuhalla, asuntotontti": {
        "filename": "purku_ja_oikeudenkayntiuhka_asuntotontti_template.docx"
    },
    "Purku- ja oikeudenkäyntiuhalla, tilapäinen yritystontti": {
        "filename": "purku_ja_oikeudenkayntiuhka_tilapainen_yritystontti_template.docx"
    },
    "Purku-uhalla, asuntotontti": {"filename": "purku_uhka_asuntotontti_template.docx"},
    "Purku-uhalla, yritystontti": {"filename": "purku_uhka_yritystontti_template.docx"},
    "Oikeudenkäyntiuhka": {"filename": "oikeudenkayntiuhka_template.docx"},
}
"""
Irtisanomis- ja oikeudenkäyntiuhalla, tilapäinen yritystontti
Purku- ja oikeudenkäyntiuhalla, asuntotontti
Purku- ja oikeudenkäyntiuhalla, tilapäinen yritystontti
Purku-uhalla, asuntotontti
Purku-uhalla, yritystontti
Oikeudenkäyntiuhka

irtisanomis_ja_oikeudenkayntiuhka_tilapainen_yritystontti_template.docx
oikeudenkayntiuhka_template.doc
purku_ja_oikeudenkayntiuhka_asuntotontti_template.docx
purku_ja_oikeudenkayntiuhka_tilapainen_yritystontti_template.docx
purku_uhka_asuntotontti_template.docx
purku_uhka_yritystontti_template.docx
"""


class IsReadableDirectory(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not os.path.isdir(values):
            raise argparse.ArgumentTypeError(
                'Directory "{}" is not a directory.'.format(values)
            )

        if os.access(values, os.R_OK):
            setattr(namespace, self.dest, values)
        else:
            raise argparse.ArgumentTypeError(
                'Directory "{}" is not readable.'.format(values)
            )


class Command(BaseCommand):
    help = "Add default collection letter templates"

    def add_arguments(self, parser):
        parser.add_argument(
            "source_directory",
            action=IsReadableDirectory,
            help="Directory holding the templates",
        )

    def check_is_directory_writable(self, directory):
        if not os.path.isdir(directory):
            self.stdout.write(
                'Directory "{}" does not exist. Please create it.'.format(directory)
            )
            return False

        try:
            fp = tempfile.TemporaryFile(dir=directory)
            fp.close()
            return True
        except PermissionError:
            self.stdout.write(
                'Can not create file in directory "{}".'.format(directory)
            )
            return False

    def handle(self, *args, **options):
        destination_path = (
            Path(settings.MEDIA_ROOT) / CollectionLetterTemplate.file.field.upload_to
        )
        if not self.check_is_directory_writable(destination_path):
            raise CommandError(
                'Directory "{}" is not writable'.format(destination_path)
            )

        source_path = Path(options["source_directory"])

        from auditlog.registry import auditlog

        auditlog.unregister(CollectionLetterTemplate)

        for name, template in TEMPLATE_NAMES.items():
            self.stdout.write(name)

            source_filename = source_path / template["filename"]
            if not source_filename.exists():
                self.stdout.write(
                    ' Template file "{}" does not exist in the source directory {}'.format(
                        template["filename"], source_path
                    )
                )
                continue

            try:
                clt = CollectionLetterTemplate.objects.get(name=name)
                self.stdout.write(" Template already exists. Overwriting.")
                destination_filename = clt.file.name
            except CollectionLetterTemplate.DoesNotExist:
                self.stdout.write(" Creating new template.")
                destination_filename = (
                    Path(CollectionLetterTemplate.file.field.upload_to)
                    / template["filename"]
                )
                CollectionLetterTemplate.objects.create(
                    name=name, file=str(destination_filename)
                )

            destination_path = Path(settings.MEDIA_ROOT) / destination_filename

            self.stdout.write(
                ' Copying "{}" to "{}"'.format(source_filename, destination_path)
            )

            copyfile(source_filename, destination_path)
