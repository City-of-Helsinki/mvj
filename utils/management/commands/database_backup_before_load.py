import subprocess

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create temporary database backups before loading data from a dump from another environment."

    def add_arguments(self, parser):
        parser.add_argument("db_name", type=str, help="Name of target database")
        parser.add_argument("db_host", type=str, help="Hostname of target database")
        parser.add_argument("db_port", type=str, help="Port of target database")
        parser.add_argument("db_user", type=str, help="Admin user of target database")

    def handle(self, *args, **kwargs):
        db_name = kwargs.get("db_name")
        db_host = kwargs.get("db_host")
        db_port = kwargs.get("db_port")
        db_user = kwargs.get("db_user")

        try:
            backup_command = f"utils/scripts/database_backup_before_load.sh {db_name} {db_host} {db_port} {db_user}"
            self.stdout.write(self.style.SUCCESS(f"Running: {backup_command}"))
            subprocess.run(
                [
                    backup_command,
                ],
                shell=True,
                check=True,
            )
            self.stdout.write(self.style.SUCCESS("Database backups completed"))

        except subprocess.CalledProcessError as e:
            raise CommandError(f"An error occurred while executing scripts: {e}")

        except Exception as e:
            raise CommandError(f"An unexpected error occurred: {e}")
