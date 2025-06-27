#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "mvj" <<-EOSQL
	CREATE EXTENSION IF NOT EXISTS postgis;
EOSQL
