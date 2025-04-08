#!/bin/bash

# Restore environment-specific database objects and settings from temporary
# database backups after loading data from a dump from another environment.

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

# Verify temporary directory exists
if [ ! -d "$TMP_DIR" ]; then
  echo "Temporary directory $TMP_DIR not found! Did you run the backup script?"
  exit 1
fi

echo "Starting database restoration operations. You may be prompted for the database password."

# Restore database ownerships and permissions
echo "Restoring database ownerships and permissions from $OWNERSHIPS_BACKUP_FILENAME..."
OWNERSHIPS_BACKUP_PATH="$TMP_DIR/$OWNERSHIPS_BACKUP_FILENAME"
if [ -f "$OWNERSHIPS_BACKUP_PATH" ]; then
  psql -d "$TARGET_DB" -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -f "$OWNERSHIPS_BACKUP_PATH"
else
  echo "WARNING: Ownerships backup file not found at $OWNERSHIPS_BACKUP_PATH"
fi

# Restore batchrun schedules as they are environment-specific
echo "Restoring batchrun job schedules from $BATCHRUN_SCHEDULEDJOB_BACKUP_FILENAME..."
BATCHRUN_SCHEDULEDJOB_BACKUP_PATH="$TMP_DIR/$BATCHRUN_SCHEDULEDJOB_BACKUP_FILENAME"
if [ -f "$BATCHRUN_SCHEDULEDJOB_BACKUP_PATH" ]; then
  # First delete existing schedules to avoid conflicts
  psql -d "$TARGET_DB" -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "TRUNCATE batchrun_scheduledjob CASCADE;"
  # Then restore the backed up schedules
  psql -d "$TARGET_DB" -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "\copy batchrun_scheduledjob FROM '$BATCHRUN_SCHEDULEDJOB_BACKUP_PATH' CSV HEADER;"
else
  echo "WARNING: Batchrun schedules backup file not found at $BATCHRUN_SCHEDULEDJOB_BACKUP_PATH"
fi

echo -e "Automated repair completed. Next steps for you: review the temporary backups, " \
  "and restore whatever you think is necessary either manually or with psql or pg_restore. Examples:\n" \
  "- admin users\n" \
  "- lessor contact names\n" \
  "- users with Export API tokens"
echo "Then lastly, delete or safekeep the temporary backups in $TMP_DIR."
