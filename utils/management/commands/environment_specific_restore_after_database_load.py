import json
import os
import subprocess

from django.contrib.auth.models import Permission
from django.core import serializers
from django.core.management.base import BaseCommand, CommandError
from rest_framework.authtoken.models import Token

from batchrun.models import ScheduledJob
from leasing.models import Contact
from users.models import User
from utils.management.commands import database_backup_script_constants as constants


class Command(BaseCommand):
    help = "Restore environment-specific database objects and settings after loading data from another environment"

    def add_arguments(self, parser):
        parser.add_argument("target_db", help="Target database name")
        parser.add_argument("db_host", help="Database host")
        parser.add_argument("db_port", help="Database port")
        parser.add_argument("db_user", help="Database user")
        parser.add_argument(
            "backup_dir", help="Path where the temporary backup files are stored"
        )
        parser.add_argument(
            "--restore-object-ownerships-and-permissions",
            action="store_true",
            default=False,
            help=(
                "Restore object ownerships and permissions."
                " Uses PSQL, which might not be available in all environments."
            ),
        )

    def handle(self, *args, **options):
        target_db = options["target_db"]
        db_host = options["db_host"]
        db_port = options["db_port"]
        db_user = options["db_user"]
        backup_dir = options["backup_dir"]
        restore_object_ownerships_and_permissions = options[
            "restore_object_ownerships_and_permissions"
        ]

        self._ensure_backup_directory(backup_dir)

        self.stdout.write(
            "Starting environment-specific database restore operations. You may be prompted for the database password."
        )
        if restore_object_ownerships_and_permissions:
            self._restore_object_ownerships_and_permissions(
                backup_dir,
                target_db,
                db_host,
                db_port,
                db_user,
                constants.OWNERSHIPS_BACKUP_FILENAME,
            )
        else:
            self.stdout.write(
                "Skipping ownership and permission restore."
                " Use --restore-object-ownerships-and-permissions to enable it."
            )
        self._restore_admin_users(backup_dir, constants.ADMIN_USERS_BACKUP_FILENAME)
        self._restore_export_api_users(
            backup_dir, constants.EXPORT_API_USERS_BACKUP_FILENAME
        )
        self._restore_lessor_contacts(
            backup_dir, constants.LESSOR_CONTACTS_BACKUP_FILENAME
        )
        self._restore_batchrun_schedules(
            backup_dir, constants.BATCHRUN_SCHEDULEDJOB_BACKUP_FILENAME
        )

        self._print_follow_up_instructions(backup_dir)

    def _ensure_backup_directory(self, backup_dir: str) -> None:
        if os.path.isdir(backup_dir):
            self.stdout.write(f"Backup directory already exists at: {backup_dir}")
            return

        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            self.stdout.write(f"Backup directory created at: {backup_dir}")
            return

        raise CommandError(f"Backup path '{backup_dir}' exists but is not a directory.")

    def _restore_object_ownerships_and_permissions(
        self,
        backup_dir: str,
        target_db: str,
        db_host: str,
        db_port: str,
        db_user: str,
        ownerships_backup_filename: str,
    ) -> None:
        ownerships_backup_path = os.path.join(backup_dir, ownerships_backup_filename)
        self.stdout.write(
            f"Restoring ownerships and permissions from {ownerships_backup_filename}..."
        )

        subprocess.run(
            [
                "psql",
                "-d",
                target_db,
                "-h",
                db_host,
                "-p",
                db_port,
                "-U",
                db_user,
                "-f",
                ownerships_backup_path,
            ],
            check=True,
        )

    def _restore_admin_users(self, backup_dir: str, filename: str) -> None:
        admin_users_backup_path = os.path.join(backup_dir, filename)
        self.stdout.write(f"Restoring admin users from {filename}...")

        with open(admin_users_backup_path, "r") as f:
            admin_user_backups = serializers.deserialize("json", f)

            for backup in admin_user_backups:
                user, created = User.objects.get_or_create(
                    username=backup.object.username,
                    password=backup.object.password,
                    first_name=backup.object.first_name,
                    last_name=backup.object.last_name,
                    email=backup.object.email,
                    is_superuser=backup.object.is_superuser,
                    is_staff=backup.object.is_staff,
                    is_active=backup.object.is_active,
                )
                if created:
                    # Restore user's service unit associations
                    user.service_units.set(backup.object.service_units.all())

                    self.stdout.write(
                        f"Admin user restored: {user.username} (ID: {user.pk})"
                    )
                else:
                    self.stdout.write(
                        f"Admin user already exists: {user.username} (ID: {user.pk})"
                    )

    def _restore_export_api_users(self, backup_dir: str, filename: str) -> None:
        export_api_users_backup_path = os.path.join(backup_dir, filename)
        self.stdout.write(f"Restoring Export API users from {filename}...")

        with open(export_api_users_backup_path, "r") as f:
            user_backups = json.load(f)

            for backup in user_backups:
                heluser_username_prefix = "u-"
                username: str = backup["username"]
                if username.startswith(heluser_username_prefix):
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipping restoration of Export API user {backup['username']} because it "
                            "is a heluser account. "
                            "Creating the user this way would break login for them."
                        )
                    )
                    continue

                user, created = User.objects.get_or_create(username=backup["username"])

                if created:
                    # Disable admin interface access
                    user.set_unusable_password()
                    user.save()

                # Restore API token
                api_key = backup["api_key"]
                Token.objects.get_or_create(user=user, key=api_key)

                # Restore API permissions
                permissions = backup.get("permissions", [])
                for codename in permissions:
                    permission = Permission.objects.get(codename=codename)
                    user.user_permissions.add(permission)

                self.stdout.write(
                    f"Export API user restored: {user.username} (ID: {user.pk})"
                )

    def _restore_lessor_contacts(self, backup_dir: str, filename: str) -> None:
        lessor_contacts_backup_path = os.path.join(backup_dir, filename)
        self.stdout.write(f"Restoring lessor contacts from {filename}...")

        with open(lessor_contacts_backup_path, "r") as f:
            contact_backups = serializers.deserialize("json", f)

            for backup in contact_backups:
                try:
                    lessor = Contact.objects.get(
                        is_lessor=True,
                        type=backup.object.type,
                        service_unit=backup.object.service_unit,
                    )
                    lessor.type = backup.object.type
                    lessor.name = backup.object.name
                    lessor.address = backup.object.address
                    lessor.postal_code = backup.object.postal_code
                    lessor.city = backup.object.city
                    lessor.email = backup.object.email
                    lessor.sap_sales_office = backup.object.sap_sales_office
                    lessor.service_unit = backup.object.service_unit
                    lessor.save()
                    self.stdout.write(
                        f"Lessor contact restored: {lessor.name} (ID: {lessor.pk})"
                    )
                except (Contact.DoesNotExist, Contact.MultipleObjectsReturned):
                    lessor = Contact.objects.create(
                        type=backup.object.type,
                        name=backup.object.name,
                        address=backup.object.address,
                        postal_code=backup.object.postal_code,
                        city=backup.object.city,
                        email=backup.object.email,
                        is_lessor=True,
                        sap_sales_office=backup.object.sap_sales_office,
                        service_unit=backup.object.service_unit,
                    )
                    self.stdout.write(
                        f"Lessor contact created: {lessor.name} (ID: {lessor.pk})"
                    )

    def _restore_batchrun_schedules(self, backup_dir: str, filename: str) -> None:
        batchrun_scheduledjob_backup_path = os.path.join(backup_dir, filename)
        self.stdout.write(f"Restoring batchrun job schedules from {filename}...")

        # Drop existing schedules that were loaded from dump
        ScheduledJob.objects.all().delete()

        with open(batchrun_scheduledjob_backup_path, "r") as f:
            schedule_backups = serializers.deserialize("json", f)
            for backup in schedule_backups:
                schedule = backup.object
                schedule.save()
                self.stdout.write(
                    f"Batchrun schedule restored: {schedule.comment} (ID: {schedule.pk})"
                )

    def _print_follow_up_instructions(self, backup_dir: str) -> None:
        self.stdout.write(
            self.style.SUCCESS(
                "Automated partial restore completed!\n"
                "Next steps for you: review the temporary backups, "
                "and restore whatever you think is necessary either manually or with psql or pg_restore."
            )
        )
        self.stdout.write(
            self.style.WARNING(
                f"Then lastly, delete the temporary backups in {backup_dir}."
            )
        )
