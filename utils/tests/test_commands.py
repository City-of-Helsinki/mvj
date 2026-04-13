from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.core.management.base import CommandError

from utils.management.commands import database_backup_script_constants as constants
from utils.management.commands.database_backup_before_load import (
    Command as BackupBeforeLoadCommand,
)
from utils.management.commands.environment_specific_restore_after_database_load import (
    Command as RestoreAfterLoadCommand,
)


@pytest.mark.parametrize(
    "command_cls", [BackupBeforeLoadCommand, RestoreAfterLoadCommand]
)
def test_ensure_backup_directory_creates_missing_directory(tmp_path: Path, command_cls):
    backup_dir = tmp_path / "tmp_backup"

    command = command_cls()
    command._ensure_backup_directory(str(backup_dir))

    assert backup_dir.exists()
    assert backup_dir.is_dir()


@pytest.mark.parametrize(
    "command_cls", [BackupBeforeLoadCommand, RestoreAfterLoadCommand]
)
def test_ensure_backup_directory_raises_if_path_is_file(tmp_path: Path, command_cls):
    backup_file = tmp_path / "not_a_directory"
    backup_file.write_text("placeholder")

    command = command_cls()

    with pytest.raises(CommandError, match="exists but is not a directory"):
        command._ensure_backup_directory(str(backup_file))


def test_backup_ownerships_and_permissions_filters_only_grant_related_lines(
    tmp_path: Path,
):
    schema_backup = tmp_path / constants.SCHEMA_BACKUP_FILENAME
    schema_backup.write_text(
        """
CREATE TABLE test_table (id int);
ALTER TABLE public.test_table OWNER TO app_user;
COMMENT ON TABLE public.test_table IS 'sample';
REVOKE ALL ON TABLE public.test_table FROM public;
GRANT SELECT ON TABLE public.test_table TO readonly;
""".strip()
        + "\n"
    )

    command = BackupBeforeLoadCommand()
    command._backup_ownerships_and_permissions(
        backup_dir=str(tmp_path),
        schema_backup_path=str(schema_backup),
        ownerships_backup_filename=constants.OWNERSHIPS_BACKUP_FILENAME,
    )

    ownerships_backup = tmp_path / constants.OWNERSHIPS_BACKUP_FILENAME
    assert ownerships_backup.exists()
    assert ownerships_backup.read_text().splitlines() == [
        "ALTER TABLE public.test_table OWNER TO app_user;",
        "REVOKE ALL ON TABLE public.test_table FROM public;",
        "GRANT SELECT ON TABLE public.test_table TO readonly;",
    ]


def test_backup_schema_uses_pg_dump_and_returns_backup_path(tmp_path: Path):
    command = BackupBeforeLoadCommand()
    target_db = "db_name_placeholder"
    db_host = "db_host_placeholder"
    db_port = "5432"
    db_user = "db_user_placeholder"

    with patch(
        "utils.management.commands.database_backup_before_load.subprocess.run"
    ) as mock_run:
        result_path = command._backup_schema(
            backup_dir=str(tmp_path),
            target_db=target_db,
            db_host=db_host,
            db_port=db_port,
            db_user=db_user,
            schema_backup_filename=constants.SCHEMA_BACKUP_FILENAME,
        )

    expected_path = str(tmp_path / constants.SCHEMA_BACKUP_FILENAME)
    assert result_path == expected_path
    mock_run.assert_called_once_with(
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
            f"--file={expected_path}",
        ],
        check=True,
    )


def test_restore_object_ownerships_and_permissions_uses_psql(tmp_path: Path):
    command = RestoreAfterLoadCommand()
    target_db = "db_name_placeholder"
    db_host = "db_host_placeholder"
    db_port = "5432"
    db_user = "db_user_placeholder"

    # Create the backup file so the existence check passes
    (tmp_path / constants.OWNERSHIPS_BACKUP_FILENAME).write_text(
        "GRANT SELECT ON foo TO bar;\n"
    )

    with patch(
        "utils.management.commands.environment_specific_restore_after_database_load.subprocess.run"
    ) as mock_run:
        command._restore_object_ownerships_and_permissions(
            backup_dir=str(tmp_path),
            target_db=target_db,
            db_host=db_host,
            db_port=db_port,
            db_user=db_user,
            ownerships_backup_filename=constants.OWNERSHIPS_BACKUP_FILENAME,
        )

    ownerships_backup_path = str(tmp_path / constants.OWNERSHIPS_BACKUP_FILENAME)
    mock_run.assert_called_once_with(
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


def test_restore_object_ownerships_and_permissions_raises_if_backup_file_missing(
    tmp_path: Path,
):
    command = RestoreAfterLoadCommand()

    with pytest.raises(CommandError, match="backup file not found"):
        command._restore_object_ownerships_and_permissions(
            backup_dir=str(tmp_path),
            target_db="placeholder",
            db_host="placeholder",
            db_port="placeholder",
            db_user="placeholder",
            ownerships_backup_filename=constants.OWNERSHIPS_BACKUP_FILENAME,
        )


def test_restore_export_api_users_skips_heluser_accounts(tmp_path: Path):
    backup_file = tmp_path / constants.EXPORT_API_USERS_BACKUP_FILENAME
    backup_file.write_text(
        '[{"username": "u-test.user", "api_key": "abc123", "permissions": ["view_thing"]}]'
    )

    command = RestoreAfterLoadCommand()

    with patch(
        "utils.management.commands.environment_specific_restore_after_database_load.User.objects.get_or_create"
    ) as mock_get_or_create_user, patch(
        "utils.management.commands.environment_specific_restore_after_database_load.Token.objects.get_or_create"
    ) as mock_get_or_create_token, patch(
        "utils.management.commands.environment_specific_restore_after_database_load.Permission.objects.get"
    ) as mock_permission_get:
        command._restore_export_api_users(
            backup_dir=str(tmp_path),
            filename=constants.EXPORT_API_USERS_BACKUP_FILENAME,
        )

    mock_get_or_create_user.assert_not_called()
    mock_get_or_create_token.assert_not_called()
    mock_permission_get.assert_not_called()


def test_restore_export_api_users_restores_user_token_and_permissions(tmp_path: Path):
    backup_file = tmp_path / constants.EXPORT_API_USERS_BACKUP_FILENAME
    backup_file.write_text(
        '[{"username": "export-user", "api_key": "abc123", "permissions": ["view_thing"]}]'
    )

    command = RestoreAfterLoadCommand()

    user = MagicMock()
    user.username = "export-user"
    user.pk = 1

    permission = MagicMock()

    with patch(
        "utils.management.commands.environment_specific_restore_after_database_load.User.objects.get_or_create",
        return_value=(user, False),
    ) as mock_get_or_create_user, patch(
        "utils.management.commands.environment_specific_restore_after_database_load.Token.objects.get_or_create"
    ) as mock_get_or_create_token, patch(
        "utils.management.commands.environment_specific_restore_after_database_load.Permission.objects.get",
        return_value=permission,
    ) as mock_permission_get:
        command._restore_export_api_users(
            backup_dir=str(tmp_path),
            filename=constants.EXPORT_API_USERS_BACKUP_FILENAME,
        )

    mock_get_or_create_user.assert_called_once_with(username="export-user")
    mock_get_or_create_token.assert_called_once_with(
        user=user, defaults={"key": "abc123"}
    )
    mock_permission_get.assert_called_once_with(codename="view_thing")
    user.user_permissions.add.assert_called_once_with(permission)


# Placeholder parameter values for the common database connection options used
# in the backup and restore command tests, to avoid unnecessary repetition.
_DB_SCRIPTS_CONNECTION_OPTIONS = {
    "target_db": "placeholder",
    "db_host": "placeholder",
    "db_port": "placeholder",
    "db_user": "placeholder",
}


@pytest.mark.parametrize("schema_flag", [True, False])
def test_backup_handle_schema_flag_enables_schema_and_ownership_backup(
    tmp_path: Path, schema_flag: bool
):
    command = BackupBeforeLoadCommand()
    options = {
        **_DB_SCRIPTS_CONNECTION_OPTIONS,
        "backup_dir": str(tmp_path),
        "schema": schema_flag,
        "binary_dump": False,
    }

    with patch.object(command, "_backup_admin_users"), patch.object(
        command, "_backup_export_api_users"
    ), patch.object(command, "_backup_batchrun_schedules"), patch.object(
        command, "_backup_lessor_contacts"
    ), patch.object(
        command, "_backup_schema"
    ) as mock_schema, patch.object(
        command, "_backup_ownerships_and_permissions"
    ) as mock_ownerships:
        command.handle(**options)

    if schema_flag:
        mock_schema.assert_called_once()
        mock_ownerships.assert_called_once()
    else:
        mock_schema.assert_not_called()
        mock_ownerships.assert_not_called()


@pytest.mark.parametrize("binary_dump_flag", [True, False])
def test_backup_handle_binary_dump_flag_enables_database_binary_backup(
    tmp_path: Path, binary_dump_flag: bool
):
    command = BackupBeforeLoadCommand()
    options = {
        **_DB_SCRIPTS_CONNECTION_OPTIONS,
        "backup_dir": str(tmp_path),
        "schema": False,
        "binary_dump": binary_dump_flag,
    }

    with patch.object(command, "_backup_admin_users"), patch.object(
        command, "_backup_export_api_users"
    ), patch.object(command, "_backup_batchrun_schedules"), patch.object(
        command, "_backup_lessor_contacts"
    ), patch.object(
        command, "_backup_database_binary"
    ) as mock_binary:
        command.handle(**options)

    if binary_dump_flag:
        mock_binary.assert_called_once()
    else:
        mock_binary.assert_not_called()


@pytest.mark.parametrize("ownerships_flag", [True, False])
def test_restore_handle_ownerships_flag_enables_ownership_restore(
    tmp_path: Path, ownerships_flag: bool
):
    command = RestoreAfterLoadCommand()
    options = {
        **_DB_SCRIPTS_CONNECTION_OPTIONS,
        "backup_dir": str(tmp_path),
        "ownerships_and_permissions": ownerships_flag,
    }

    with patch.object(
        command, "_restore_object_ownerships_and_permissions"
    ) as mock_ownerships, patch.object(command, "_restore_admin_users"), patch.object(
        command, "_restore_export_api_users"
    ), patch.object(
        command, "_restore_lessor_contacts"
    ), patch.object(
        command, "_restore_batchrun_schedules"
    ), patch.object(
        command, "_print_follow_up_instructions"
    ):
        command.handle(**options)

    if ownerships_flag:
        mock_ownerships.assert_called_once()
    else:
        mock_ownerships.assert_not_called()
