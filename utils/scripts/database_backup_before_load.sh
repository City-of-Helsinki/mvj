#!/bin/bash

# Script to backup any environment-specific data and settings from the database
# before loading a database dump e.g. from production data.

# Shell settings for error handling
set -e
set -u

# Configuration passed as an arguments
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

# Source some variables shared by backup and restore scripts
SCRIPT_DIR=$(dirname "$0")
VARIABLES_FILENAME="$SCRIPT_DIR/database_backup_restore.var"
if [ -f "$VARIABLES_FILENAME" ]; then
    source "$VARIABLES_FILENAME"
else
    echo "Variables file $VARIABLES_FILENAME not found!"
    exit 1
fi

# Create a temporary directory for backups
if [ ! -d "$TMP_DIR" ]; then
    mkdir -p "$TMP_DIR"
    echo "Directory created at: $TMP_DIR"
else
    echo "Directory already exists at: $TMP_DIR"
fi

echo "Temporary directory created at: $TMP_DIR"

# Backup object ownerships
pg_dump -d "$TARGET_DB" -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" --schema-only --file="$TMP_DIR/$SCHEMA_BACKUP_FILENAME"

# Backup admin users
psql -d "$TARGET_DB" -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "\copy (SELECT * FROM users_user WHERE is_staff=true) TO '$TMP_DIR/$ADMIN_USERS_BACKUP_FILENAME' CSV HEADER;"

# Backup batchrun schedules
psql -d "$TARGET_DB" -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "\copy batchrun_scheduledjob TO '$TMP_DIR/$BATCHRUN_SCHEDULEDJOB_BACKUP_FILENAME' CSV HEADER;"

echo "Backup completed."
