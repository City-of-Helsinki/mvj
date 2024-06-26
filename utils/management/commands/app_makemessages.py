from django.core.management.commands import makemessages


class Command(makemessages.Command):
    msgmerge_options = [
        "-q",
        "--previous",
        "--update",
        "--backup=none",
        "--no-fuzzy-matching",
    ]

    def handle(self, *args, **options):
        options["no_location"] = True
        options["no_obsolete"] = True
        options["ignore_patterns"] = ["venv"]
        super(Command, self).handle(*args, **options)
