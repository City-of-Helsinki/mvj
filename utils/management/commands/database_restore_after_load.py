import subprocess

from django.core.management.base import BaseCommand, CommandError

ENTIRE_TABLES_TO_RESTORE = []

TABLES_TO_RESTORE_ROWS_ONLY = []


class Command(BaseCommand):
    help = (
        "Restore necessary database objects from temporary database backups "
        "after loading data from a dump from another environment"
    )

    def add_arguments(self, parser):
        parser.add_argument("db_name", type=str, help="Name of target database")
        parser.add_argument(
            "backup_dump_name",
            type=str,
            help="Name of the target DB backup dump file to restore entire tables from",
        )
        parser.add_argument(
            "old_db_owner",
            type=str,
            help="Name of old owner of the database objects in the incoming dump",
        )
        parser.add_argument(
            "new_db_owner",
            type=str,
            help="Name of new owner of the loaded database objects",
        )

    def handle(self, *args, **kwargs):
        db_name = kwargs["target_db_name"]
        old_db_owner = kwargs["old_db_owner"]
        new_db_owner = kwargs["new_db_owner"]

        try:
            restore_command = f"./database_restore_after_load.sh {db_name} {old_db_owner} {new_db_owner}"
            self.stdout.write(self.style.SUCCESS(f"Running: {restore_command}"))
            subprocess.run(restore_command, shell=True, check=True)

            self.stdout.write(self.style.SUCCESS("Database restores completed"))

        except subprocess.CalledProcessError as e:
            raise CommandError(f"An error occurred while executing scripts: {e}")

        except Exception as e:
            raise CommandError(f"An unexpected error occurred: {e}")
