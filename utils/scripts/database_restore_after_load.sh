




############### TODO FIX EVERYTHING based on the backup script
























#!/bin/bash

set -e
set -u

# Script to restore any environment-specific data and settings to the database
# after loading a database dump e.g. from production data.

# Configuration passed as an argument
TARGET_DB="$1"  # Target database name
OLD_DB_OWNER="$2"  # Old database owner from the incoming dump
NEW_DB_OWNER="$3"  # New database owner from existing DB configuration

# Ensure target database is specified
if [ -z "$TARGET_DB" ]; then
  echo "Please provide the target database name as an argument."
  exit 1
fi
if [ -z "$INCOMING_DB_OWNER" ]; then
  echo "Please provide the  database owner as 2nd argument."
  exit 1
fi
if [ -z "$NEW_DB_OWNER" ]; then
  echo "Please provide the new database owner as 3rd argument."
  exit 1
fi

# Restore ownerships (requires manual intervention to match ownerships from backup)
psql -U postgres -d "$TARGET_DB" -f "ownership_backup.sql"

# or use raw SQL, might not work for all environments
# DO $$
# DECLARE
#     t text;
# BEGIN
#     FOR t IN
#         SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tableowner = 'postgres' AND tablename NOT IN ('spatial_ref_sys');
#     LOOP
#         EXECUTE format('ALTER TABLE public.%I OWNER TO "mvj-api-dev"', t);
#     END LOOP;
# END;
# $$;

# Restore admin users
USER_BACKUP_FILENAME="admin_users_backup.csv"
psql -U postgres -d "$TARGET_DB" -c "\copy users_user FROM 'admin_users_backup.csv' CSV HEADER;"

# Restore batchrun schedules
psql -U postgres -d "$TARGET_DB" -c "\copy batchrun_scheduledrun FROM 'batchrun_backup.csv' CSV HEADER;"

# Optionally restore specific tables from custom dump
CUSTOM_DUMP_FILE="custom_dump_file.dump"
TABLES_TO_RESTORE=("table1" "table2")  # Specify tables to restore

for TABLE in "${TABLES_TO_RESTORE[@]}"; do
  pg_restore -U postgres --data-only --table="$TABLE" --dbname="$TARGET_DB" "$CUSTOM_DUMP_FILE"
done

echo "Restoration completed."

