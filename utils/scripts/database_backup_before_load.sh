#!/bin/bash

# Creates temporary database backups before loading data from a dump from another environment.

# Shell settings for error handling
set -euo pipefail

# Hardcoded configuration
# Shell script variables file
VARIABLES_FILENAME="database_backup_scripts_shared.var"

# Configuration passed as arguments
TARGET_DB="$1"  # Target database name
DB_HOST="$2"  # Database host
DB_PORT="$3"  # Database port
DB_USER="$4"  # Database user

# Ensure arguments are specified
if [ -z "$TARGET_DB" ]; then
  echo "Please provide the target database name as 1st argument."
  exit 1
fi
if [ -z "$DB_HOST" ]; then
  echo "Please provide the database host as 2nd argument."
  exit 1
fi
if [ -z "$DB_PORT" ]; then
  echo "Please provide the database port as 3rd argument."
  exit 1
fi
if [ -z "$DB_USER" ]; then
  echo "Please provide the database user as 4th argument."
  exit 1
fi

# Source the variables shared by backup and restore scripts
SCRIPT_DIR=$(dirname "$0")
VARIABLES_PATH="$SCRIPT_DIR/$VARIABLES_FILENAME"
if [ -f "$VARIABLES_PATH" ]; then
  source "$VARIABLES_PATH"
else
  echo "Variables file $VARIABLES_FILENAME not found in $SCRIPT_DIR!"
  exit 1
fi

# Create a temporary directory for backups
if [ ! -d "$TMP_DIR" ]; then
  mkdir -p "$TMP_DIR"
  echo "Temporary directory created at: $TMP_DIR"
else
  echo "Temporary directory already exists at: $TMP_DIR"
fi

echo "Starting database backup operations. You may be prompted for the database password."

# Backup admin users, to preserve access to the admin interface
echo "Backing up admin users to $ADMIN_USERS_BACKUP_FILENAME..."
ADMIN_USERS_BACKUP_PATH="$TMP_DIR/$ADMIN_USERS_BACKUP_FILENAME"
psql -d "$TARGET_DB" -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "\copy (SELECT * FROM users_user WHERE is_staff=true) TO '$ADMIN_USERS_BACKUP_PATH' CSV HEADER;"

# Backup batchrun schedules, because they might be environment-specific
echo "Backing up batchrun job schedules to $BATCHRUN_SCHEDULEDJOB_BACKUP_FILENAME..."
BATCHRUN_SCHEDULEDJOB_BACKUP_PATH="$TMP_DIR/$BATCHRUN_SCHEDULEDJOB_BACKUP_FILENAME"
psql -d "$TARGET_DB" -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "\copy batchrun_scheduledjob TO '$BATCHRUN_SCHEDULEDJOB_BACKUP_PATH' CSV HEADER;"

# Backup lessor contacts, because they are Helsinki entities that should not be sanitized
echo "Backing up lessor contacts to $LESSOR_CONTACTS_BACKUP_FILENAME..."
LESSOR_CONTACTS_BACKUP_PATH="$TMP_DIR/$LESSOR_CONTACTS_BACKUP_FILENAME"
psql -d "$TARGET_DB" -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "\copy (SELECT * FROM leasing_contact WHERE is_lessor=true) TO '$LESSOR_CONTACTS_BACKUP_PATH' CSV HEADER;"

# Backup the entire database as a binary format dump file.
echo "Backing up entire database to $BINARY_DUMP_FILENAME..."
BINARY_DUMP_PATH="$TMP_DIR/$BINARY_DUMP_FILENAME"
pg_dump -d "$TARGET_DB" -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" --format="custom" --file="$BINARY_DUMP_PATH"

# Backup the database schema, to preserve ownerships and permissions
echo "Backing up database schema to $SCHEMA_BACKUP_FILENAME..."
SCHEMA_BACKUP_PATH="$TMP_DIR/$SCHEMA_BACKUP_FILENAME"
pg_dump -d "$TARGET_DB" -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" --schema-only --file="$SCHEMA_BACKUP_PATH"

# Backup database object ownerships and permissions separately
echo "Filtering only ownership and permission modifications to $OWNERSHIPS_BACKUP_FILENAME..."
OWNERSHIPS_BACKUP_PATH="$TMP_DIR/$OWNERSHIPS_BACKUP_FILENAME"
grep -E 'ALTER .* OWNER TO' "$SCHEMA_BACKUP_PATH" > "$OWNERSHIPS_BACKUP_PATH"
grep -E 'REVOKE .* FROM' "$SCHEMA_BACKUP_PATH" >> "$OWNERSHIPS_BACKUP_PATH"
grep -E 'GRANT .* TO' "$SCHEMA_BACKUP_PATH" >> "$OWNERSHIPS_BACKUP_PATH"

# Possibilities for future additions to the backup process:
# - users with Export API tokens

echo "Backup completed."
