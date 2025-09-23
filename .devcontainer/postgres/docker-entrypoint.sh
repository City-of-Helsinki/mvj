#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" -p "$POSTGRES_PORT"; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 1
done

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "mvj-db" --port "$POSTGRES_PORT" <<-EOSQL
	CREATE EXTENSION IF NOT EXISTS postgis;
EOSQL
