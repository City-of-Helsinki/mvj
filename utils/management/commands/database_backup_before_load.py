import json
import os
import re
import subprocess

from django.core import serializers
from django.core.management.base import BaseCommand, CommandError
from rest_framework.authtoken.models import Token

from batchrun.models import ScheduledJob
from leasing.models import Contact
from users.models import User
from utils.management.commands import database_backup_script_constants as constants


class Command(BaseCommand):
    help = "Creates temporary database backups before loading data from a dump from another environment"

    def add_arguments(self, parser):
        parser.add_argument("target_db", help="Target database name")
        parser.add_argument("db_host", help="Database host")
        parser.add_argument("db_port", help="Database port")
        parser.add_argument("db_user", help="Database user")
        parser.add_argument(
            "backup_dir", help="Path where to store these temporary backup files"
        )
        parser.add_argument(
            "--binary-dump",
            action="store_true",
            help="Also create a binary database dump with pg_dump --format=custom",
        )

    def handle(self, *args, **options):
        target_db = options["target_db"]
        db_host = options["db_host"]
        db_port = options["db_port"]
        db_user = options["db_user"]
        backup_dir = options["backup_dir"]
        backup_binary_dump = options["binary_dump"]

        self._ensure_backup_directory(backup_dir)

        self.stdout.write(
            "Starting database backup operations. You may be prompted for the database password."
        )
        self._backup_admin_users(backup_dir, constants.ADMIN_USERS_BACKUP_FILENAME)
        self._backup_export_api_users(
            backup_dir, constants.EXPORT_API_USERS_BACKUP_FILENAME
        )
        self._backup_batchrun_schedules(
            backup_dir, constants.BATCHRUN_SCHEDULEDJOB_BACKUP_FILENAME
        )
        self._backup_lessor_contacts(
            backup_dir, constants.LESSOR_CONTACTS_BACKUP_FILENAME
        )

        schema_backup_path = self._backup_schema(
            backup_dir,
            target_db,
            db_host,
            db_port,
            db_user,
            constants.SCHEMA_BACKUP_FILENAME,
        )
        self._backup_ownerships_and_permissions(
            backup_dir, schema_backup_path, constants.OWNERSHIPS_BACKUP_FILENAME
        )
        if backup_binary_dump:
            self._backup_database_binary(
                backup_dir,
                target_db,
                db_host,
                db_port,
                db_user,
                constants.BINARY_DUMP_FILENAME,
            )
        else:
            self.stdout.write(
                "Skipping binary database dump. Use --binary-dump to enable it."
            )

        self.stdout.write(self.style.SUCCESS("Backup completed."))

    def _ensure_backup_directory(self, backup_dir: str) -> None:
        if os.path.isdir(backup_dir):
            self.stdout.write(f"Backup directory already exists at: {backup_dir}")
            return

        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            self.stdout.write(f"Backup directory created at: {backup_dir}")
            return

        raise CommandError(f"Backup path '{backup_dir}' exists but is not a directory.")

    def _backup_admin_users(self, backup_dir: str, filename: str) -> None:
        """Back up active admin users, excluding those with password set to '!'.

        Password "!" means that the users was already sanitized before, and
        doesn't contain useful information anymore.
        """
        admin_users_backup_path = os.path.join(backup_dir, filename)
        self.stdout.write(f"Backing up admin users to {filename}...")

        sanitized_password_default = "!"
        admin_users = User.objects.filter(is_staff=True, is_active=True).exclude(
            password=sanitized_password_default
        )

        with open(admin_users_backup_path, "w") as f:
            serializers.serialize("json", admin_users, stream=f, indent=2)

    def _backup_export_api_users(self, backup_dir: str, filename: str) -> None:
        """Back up export API users, including their permissions and API tokens.

        Uses custom JSON format to include related data.
        """
        export_api_users_backup_path = os.path.join(backup_dir, filename)
        self.stdout.write(f"Backing up export API users to {filename}...")

        api_tokens = Token.objects.all()

        user_data: list[dict] = []
        for token in api_tokens:
            user = token.user
            user_permissions_codenames = [
                permission.codename for permission in user.user_permissions.all()
            ]
            user_data.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "permissions": user_permissions_codenames,
                    "api_key": token.key,
                }
            )

        with open(export_api_users_backup_path, "w") as f:
            json.dump(user_data, f, indent=2)

    def _backup_batchrun_schedules(self, backup_dir: str, filename: str) -> None:
        batchrun_scheduledjob_backup_path = os.path.join(backup_dir, filename)
        self.stdout.write(f"Backing up batchrun job schedules to {filename}...")

        schedules = ScheduledJob.objects.all()

        with open(batchrun_scheduledjob_backup_path, "w") as f:
            serializers.serialize("json", schedules, stream=f, indent=2)

    def _backup_lessor_contacts(self, backup_dir: str, filename: str) -> None:
        lessor_contacts_backup_path = os.path.join(backup_dir, filename)
        self.stdout.write(f"Backing up lessor contacts to {filename}...")

        contacts = Contact.objects.filter(is_lessor=True)

        with open(lessor_contacts_backup_path, "w") as f:
            serializers.serialize("json", contacts, stream=f, indent=2)

    def _backup_schema(
        self,
        backup_dir: str,
        target_db: str,
        db_host: str,
        db_port: str,
        db_user: str,
        schema_backup_filename: str,
    ) -> str:
        schema_backup_path = os.path.join(backup_dir, schema_backup_filename)
        self.stdout.write(f"Backing up database schema to {schema_backup_filename}...")
        subprocess.run(
            [
                "pg_dump",
                "-d",
                target_db,
                "-h",
                db_host,
                "-p",
                db_port,
                "-U",
                db_user,
                "--schema-only",
                "--file=" + schema_backup_path,
            ],
            check=True,
        )
        return schema_backup_path

    def _backup_ownerships_and_permissions(
        self,
        backup_dir: str,
        schema_backup_path: str,
        ownerships_backup_filename: str,
    ) -> None:
        if not os.path.exists(schema_backup_path):
            raise CommandError(
                f"Schema backup file {schema_backup_path} does not exist."
            )

        ownerships_backup_path = os.path.join(backup_dir, ownerships_backup_filename)
        self.stdout.write(
            f"Filtering only ownership and permission modifications to {ownerships_backup_filename}..."
        )
        with open(schema_backup_path, "r") as schema_file, open(
            ownerships_backup_path, "w"
        ) as ownership_file:
            for line in schema_file:
                ownership_patterns = [
                    re.compile(r"ALTER\s+.*\s+OWNER\s+TO"),
                    re.compile(r"REVOKE\s+.*\s+FROM"),
                    re.compile(r"GRANT\s+.*\s+TO"),
                ]

                if any(pattern.search(line) for pattern in ownership_patterns):
                    ownership_file.write(line)

    def _backup_database_binary(
        self,
        backup_dir: str,
        target_db: str,
        db_host: str,
        db_port: str,
        db_user: str,
        binary_dump_filename: str,
    ) -> None:
        """Backup the entire database to a binary dump file."""
        binary_dump_path = os.path.join(backup_dir, binary_dump_filename)
        self.stdout.write(f"Backing up entire database to {binary_dump_filename}...")
        subprocess.run(
            [
                "pg_dump",
                "-d",
                target_db,
                "-h",
                db_host,
                "-p",
                db_port,
                "-U",
                db_user,
                "--format=custom",
                "--file=" + binary_dump_path,
            ],
            check=True,
        )
